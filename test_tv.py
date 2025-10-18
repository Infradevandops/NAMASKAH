import os
import requests

# Read from .env manually
with open('.env', 'r') as f:
    for line in f:
        if line.startswith('TEXTVERIFIED_API_KEY='):
            API_KEY = line.split('=', 1)[1].strip()
        elif line.startswith('TEXTVERIFIED_EMAIL='):
            EMAIL = line.split('=', 1)[1].strip()

print(f"API Key: {API_KEY[:20]}...")
print(f"Email: {EMAIL}")

# Get token
headers = {"X-API-KEY": API_KEY, "X-API-USERNAME": EMAIL}
r = requests.post("https://www.textverified.com/api/pub/v2/auth", headers=headers)
print(f"\nAuth status: {r.status_code}")

if r.status_code == 200:
    token = r.json()["token"]
    print(f"Token: {token[:20]}...")
    
    # Try to create verification
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"serviceName": "whatsapp", "capability": "sms"}
    
    r = requests.post(
        "https://www.textverified.com/api/pub/v2/verifications",
        headers=headers,
        json=payload
    )
    print(f"\nCreate verification status: {r.status_code}")
    print(f"Response: {r.text}")
    
    if r.status_code == 201:
        verification_id = r.headers.get("Location", "").split("/")[-1]
        print(f"Verification ID: {verification_id}")
else:
    print(f"Auth failed: {r.text}")
