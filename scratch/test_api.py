import requests
import json

url = "http://localhost:8000/api/feedback"
data = {
    "name": "Local Test",
    "email": "local@test.com",
    "message": "Testing the local API endpoint after fix."
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
