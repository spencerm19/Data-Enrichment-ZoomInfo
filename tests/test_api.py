from fastapi.testclient import TestClient
import io

def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_upload_file(test_client, sample_csv, mock_zoominfo_response):
    with open(sample_csv, 'rb') as f:
        response = test_client.post(
            "/upload",
            files={"file": ("test.csv", f, "text/csv")}
        )
    assert response.status_code == 200
    assert "result" in response.json()

def test_upload_invalid_file(test_client):
    response = test_client.post(
        "/upload",
        files={"file": ("test.txt", io.BytesIO(b"invalid"), "text/plain")}
    )
    assert response.status_code == 400  # Bad request for non-CSV file 