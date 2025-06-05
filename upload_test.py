import requests

def upload_file(file_path, url="http://10.0.10.163:8888/upload"):
    """Upload a file to the specified endpoint"""
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'text/csv')}
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    upload_file("SampleTesting.csv") 