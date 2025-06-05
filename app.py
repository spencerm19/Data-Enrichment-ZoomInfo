import json
import logging
from enrichment import (
    enrich_data,
    ConfigurationError,
    APIError,
    DataProcessingError
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_response(status_code: int, message: str, details: dict = None) -> dict:
    """Create a standardized API response"""
    body = {
        'message': message
    }
    if details:
        body.update(details)
    
    return {
        'statusCode': status_code,
        'body': json.dumps(body)
    }

def lambda_handler(event, context):
    """
    AWS Lambda handler for data enrichment
    :param event: AWS Lambda event (S3 trigger)
    :param context: AWS Lambda context
    :return: dict with statusCode and body
    """
    try:
        # Log the received event
        logger.info("Received event: %s", json.dumps(event))
        
        # Get S3 bucket and key from event
        try:
            bucket = event['Records'][0]['s3']['bucket']['name']
            key = event['Records'][0]['s3']['object']['key']
        except (KeyError, IndexError) as e:
            return create_response(400, "Invalid event structure", {
                'error': 'Missing required S3 event data',
                'details': str(e)
            })
        
        # Process the file
        result = enrich_data(bucket, key)
        
        return create_response(200, "Data enrichment completed successfully", {
            'input_file': key,
            'output_file': result['output_file'],
            'records_processed': result['records_processed'],
            'total_records': result.get('total_records', 0)
        })
        
    except ConfigurationError as e:
        logger.error("Configuration error: %s", str(e))
        return create_response(500, "Configuration error", {
            'error_type': 'configuration_error',
            'details': str(e)
        })
        
    except APIError as e:
        logger.error("API error: %s", str(e))
        return create_response(500, "API error", {
            'error_type': 'api_error',
            'details': str(e)
        })
        
    except DataProcessingError as e:
        logger.error("Data processing error: %s", str(e))
        return create_response(500, "Data processing error", {
            'error_type': 'data_processing_error',
            'details': str(e)
        })
        
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        return create_response(500, "Internal server error", {
            'error_type': 'unexpected_error',
            'details': str(e)
        }) 