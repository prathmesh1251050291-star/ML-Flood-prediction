import requests

# Test the API endpoint
try:
    response = requests.get('http://127.0.0.1:8000/api/predict')
    print("GET request status:", response.status_code)
    if response.status_code == 200:
        print("API is working!")
    else:
        print("API returned error:", response.text)
except Exception as e:
    print("Error connecting to API:", str(e))