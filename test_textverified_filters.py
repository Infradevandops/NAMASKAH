#!/usr/bin/env python3
"""Test TextVerified API filtering options"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TEXTVERIFIED_API_KEY")
EMAIL = os.getenv("TEXTVERIFIED_EMAIL")
BASE_URL = "https://www.textverified.com"

def get_token():
    """Get auth token"""
    headers = {"X-API-KEY": API_KEY, "X-API-USERNAME": EMAIL}
    r = requests.post(f"{BASE_URL}/api/pub/v2/auth", headers=headers)
    r.raise_for_status()
    return r.json()["token"]

def test_filter(filter_name, filter_value):
    """Test a specific filter parameter"""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "serviceName": "telegram",
        "capability": "sms",
        filter_name: filter_value
    }
    
    print(f"\n{'='*60}")
    print(f"Testing: {filter_name} = {filter_value}")
    print(f"{'='*60}")
    print(f"Payload: {payload}")
    
    try:
        r = requests.post(
            f"{BASE_URL}/api/pub/v2/verifications",
            headers=headers,
            json=payload
        )
        
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:200]}")
        
        if r.status_code == 201 or r.status_code == 200:
            print(f"✅ {filter_name} is SUPPORTED!")
            verification_id = r.headers.get("Location", "").split("/")[-1]
            
            # Get verification details
            details = requests.get(
                f"{BASE_URL}/api/pub/v2/verifications/{verification_id}",
                headers=headers
            ).json()
            print(f"Number: {details.get('number')}")
            
            # Cancel it
            requests.post(
                f"{BASE_URL}/api/pub/v2/verifications/{verification_id}/cancel",
                headers=headers
            )
            return True
        else:
            print(f"❌ {filter_name} NOT supported or invalid value")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_all_filters():
    """Test all possible filter options"""
    
    print("\n" + "="*60)
    print("TEXTVERIFIED API FILTER TESTING")
    print("="*60)
    
    filters_to_test = [
        # Area code
        ("areaCode", "212"),
        ("area_code", "212"),
        ("areacode", "212"),
        
        # Carrier/ISP
        ("carrier", "verizon"),
        ("carrier", "att"),
        ("carrier", "tmobile"),
        ("isp", "verizon"),
        ("provider", "verizon"),
        
        # Region
        ("region", "US-NY"),
        ("region", "US"),
        ("state", "NY"),
        ("country", "US"),
        ("countryCode", "US"),
        
        # Number type
        ("numberType", "mobile"),
        ("type", "mobile"),
        
        # Other
        ("prefix", "212"),
        ("npa", "212"),
    ]
    
    supported = []
    not_supported = []
    
    for filter_name, filter_value in filters_to_test:
        if test_filter(filter_name, filter_value):
            supported.append(filter_name)
        else:
            not_supported.append(filter_name)
    
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    print(f"\n✅ SUPPORTED FILTERS ({len(supported)}):")
    for f in supported:
        print(f"  - {f}")
    
    print(f"\n❌ NOT SUPPORTED ({len(not_supported)}):")
    for f in not_supported:
        print(f"  - {f}")

if __name__ == "__main__":
    test_all_filters()
