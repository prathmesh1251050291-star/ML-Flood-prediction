import requests

try:
    response = requests.get('http://127.0.0.1:8000/')
    print("GET / status:", response.status_code)
    if response.status_code == 200:
        print("Root path is accessible")
    else:
        print("Error:", response.text)
except Exception as e:
    print("Error:", str(e))