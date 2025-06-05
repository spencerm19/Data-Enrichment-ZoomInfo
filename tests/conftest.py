import pytest
from fastapi.testclient import TestClient
from main import app
import os
from unittest.mock import patch
import json

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing"""
    os.environ['ZOOMINFO_CLIENT_ID'] = 'test_client_id'
    os.environ['ZOOMINFO_PRIVATE_KEY'] = 'test_private_key'
    yield
    # Clean up
    del os.environ['ZOOMINFO_CLIENT_ID']
    del os.environ['ZOOMINFO_PRIVATE_KEY']

@pytest.fixture
def mock_zoominfo_response():
    """Mock successful ZoomInfo API responses"""
    with patch('requests.post') as mock_auth, \
         patch('requests.get') as mock_search:
        # Mock authentication response
        mock_auth.return_value.status_code = 200
        mock_auth.return_value.json.return_value = {'jwt': 'test_token'}
        
        # Mock search response
        mock_search.return_value.status_code = 200
        mock_search.return_value.json.return_value = {
            'companies': [{
                'website': 'test.com',
                'industry': 'Technology',
                'revenue': '1M-10M',
                'employeeCount': '1-10',
                'hqLocation': {'city': 'Test City'}
            }]
        }
        yield

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def sample_csv(tmp_path):
    csv_content = "company_name\nMicrosoft\nGoogle\nApple"
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(csv_content)
    return csv_file 