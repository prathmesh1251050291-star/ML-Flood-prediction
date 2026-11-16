import requests

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