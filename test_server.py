import time
import requests

# Wait for server to be ready
time.sleep(5)

try:
    response = requests.post('http://127.0.0.1:8000/api/predict', json={
        'location': 'Rasuwagadhi', 
        'season': 'Monsoon', 
        'today_rainfall_mm': 65, 
        'yesterday_rainfall_mm': 20, 
        'prior3_rainfall_mm': 40, 
        'yesterday_soil_moisture': 0.35
    })
    print("Status Code:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Error:", str(e))