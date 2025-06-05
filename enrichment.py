import os
import json
import logging
import pandas as pd
import requests
from typing import Dict, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class EnrichmentError(Exception):
    """Base exception for enrichment errors"""
    pass

class ConfigurationError(EnrichmentError):
    """Raised when there's a configuration issue"""
    pass

class APIError(EnrichmentError):
    """Raised when there's an API-related error"""
    pass

class DataProcessingError(EnrichmentError):
    """Raised when there's a data processing error"""
    pass

def get_zoominfo_credentials() -> Dict[str, str]:
    """
    Get ZoomInfo credentials from environment variables
    
    Returns:
        Dict with client_id and private_key
    
    Raises:
        ConfigurationError: If credentials are not set
    """
    client_id = os.getenv('ZOOMINFO_CLIENT_ID')
    private_key = os.getenv('ZOOMINFO_PRIVATE_KEY')
    
    if not client_id or not private_key:
        msg = "Missing ZoomInfo credentials in environment variables"
        logging.error(msg)
        raise ConfigurationError(msg)
            
    return {
        'client_id': client_id,
        'private_key': private_key
    }

def get_zoominfo_token(credentials: Dict[str, str]) -> str:
    """
    Get ZoomInfo API token using client credentials flow
    
    Args:
        credentials: Dict with client_id and private_key
    
    Returns:
        JWT token string
    
    Raises:
        APIError: If token cannot be obtained
    """
    auth_url = "https://api.zoominfo.com/authenticate"
    try:
        auth_data = {
            "clientId": credentials['client_id'],
            "privateKey": credentials['private_key']
        }
        response = requests.post(auth_url, json=auth_data)
        response.raise_for_status()
        return response.json()['jwt']
    except requests.exceptions.RequestException as e:
        msg = f"Failed to authenticate with ZoomInfo API: {str(e)}"
        logging.error(msg)
        raise APIError(msg) from e

def enrich_company_data(company_name: str, token: str) -> Optional[Dict[str, Any]]:
    """
    Enrich company data using ZoomInfo API
    
    Args:
        company_name: Name of the company to enrich
        token: ZoomInfo API token
    
    Returns:
        Dict with enriched data or None if company not found
    
    Raises:
        APIError: If API call fails
    """
    search_url = "https://api.zoominfo.com/search/company"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"companyName": company_name}
    
    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get('companies') and len(data['companies']) > 0:
            company = data['companies'][0]
            return {
                'website': company.get('website'),
                'industry': company.get('industry'),
                'revenue': company.get('revenue'),
                'employee_count': company.get('employeeCount'),
                'hq_location': company.get('hqLocation', {}).get('city')
            }
        logging.info(f"No data found for company: {company_name}")
        return None
    except requests.exceptions.RequestException as e:
        msg = f"Error enriching data for {company_name}: {str(e)}"
        logging.warning(msg)
        if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 401:
            raise APIError("ZoomInfo API token expired or invalid") from e
        return None

def enrich_data(file_path: str) -> Dict[str, Any]:
    """
    Main function to enrich data from CSV file
    
    Args:
        file_path: Path to the local CSV file
    
    Returns:
        Dict with output file path and records processed
    
    Raises:
        ConfigurationError: If configuration is invalid
        APIError: If API calls fail
        DataProcessingError: If data processing fails
    """
    try:
        # Get ZoomInfo credentials and token
        credentials = get_zoominfo_credentials()
        token = get_zoominfo_token(credentials)
        
        # Read input CSV
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise DataProcessingError(f"Error reading CSV file: {str(e)}") from e
        
        # Validate input data
        if 'company_name' not in df.columns:
            raise DataProcessingError("Input CSV must have a 'company_name' column")
        
        # Initialize new columns
        enrichment_columns = ['website', 'industry', 'revenue', 'employee_count', 'hq_location']
        for col in enrichment_columns:
            df[f'enriched_{col}'] = None
        
        # Process each company
        records_processed = 0
        total_records = len(df)
        
        for idx, row in df.iterrows():
            company_name = row['company_name']
            if not isinstance(company_name, str) or not company_name.strip():
                logging.warning(f"Invalid company name at row {idx + 1}, skipping")
                continue
                
            enriched_data = enrich_company_data(company_name.strip(), token)
            
            if enriched_data:
                for col in enrichment_columns:
                    df.at[idx, f'enriched_{col}'] = enriched_data[col]
                records_processed += 1
            
            # Log progress every 10% of records
            if (idx + 1) % max(1, total_records // 10) == 0:
                logging.info(f"Processed {idx + 1}/{total_records} records ({records_processed} enriched)...")
        
        # Generate output file name
        output_file = f"enriched_{os.path.basename(file_path)}"
        output_path = os.path.join(os.path.dirname(file_path), output_file)
        
        # Save enriched CSV
        df.to_csv(output_path, index=False)
        
        return {
            'output_file': output_path,
            'records_processed': records_processed,
            'total_records': total_records
        }
        
    except Exception as e:
        if not isinstance(e, EnrichmentError):
            logging.error(f"Unexpected error in enrich_data: {str(e)}", exc_info=True)
            raise DataProcessingError(f"Unexpected error: {str(e)}") from e
        raise 