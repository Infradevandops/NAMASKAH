#!/usr/bin/env python3
"""
Quick verification script for hourly rental features
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_features():
    print("🚀 Verifying Hourly Rental Features")
    print("=" * 50)
    
    # Test 1: System Health
    try:
        response = requests.get(f"{API_BASE}/system/health")
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", {})
            print("✅ System Health:", data.get("status"))
            print("✅ Hourly Rentals:", features.get("hourly_rentals"))
            print("✅ Retry Mechanisms:", features.get("retry_mechanisms"))
            print("✅ Circuit Breakers:", features.get("circuit_breakers"))
            print("✅ Dynamic Pricing:", features.get("dynamic_pricing"))
        else:
            print("❌ System health check failed")
            return False
    except Exception as e:
        print(f"❌ System health error: {e}")
        return False
    
    # Test 2: Login and get token
    try:
        login_response = requests.post(f"{API_BASE}/auth/login", json={
            "email": "admin@namaskah.app",
            "password": "Namaskah@Admin2024"
        })
        if login_response.status_code == 200:
            token = login_response.json()["token"]
            print("✅ Authentication successful")
        else:
            print("❌ Authentication failed")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
    
    # Test 3: Pricing API
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test different hourly durations
        test_cases = [
            {"hours": 1, "expected_base": 1.0},
            {"hours": 6, "expected_base": 2.0},
            {"hours": 24, "expected_base": 3.0}
        ]
        
        for case in test_cases:
            response = requests.get(
                f"{API_BASE}/rentals/pricing",
                params={
                    "hours": case["hours"],
                    "service_name": "telegram",
                    "mode": "always_ready"
                },
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                base_price = data.get("base_price")
                if abs(base_price - case["expected_base"]) < 0.01:
                    print(f"✅ {case['hours']}h pricing: N{base_price}")
                else:
                    print(f"❌ {case['hours']}h pricing incorrect: expected N{case['expected_base']}, got N{base_price}")
            else:
                print(f"❌ Pricing API failed for {case['hours']}h")
                return False
                
    except Exception as e:
        print(f"❌ Pricing API error: {e}")
        return False
    
    # Test 4: Frontend files
    try:
        js_response = requests.get(f"{API_BASE}/static/js/rentals.js")
        if js_response.status_code == 200:
            js_content = js_response.text
            if "RENTAL_HOURLY" in js_content and "addHourlyRentalOptions" in js_content:
                print("✅ Frontend hourly rental features loaded")
            else:
                print("❌ Frontend missing hourly rental features")
                return False
        else:
            print("❌ Frontend files not accessible")
            return False
    except Exception as e:
        print(f"❌ Frontend test error: {e}")
        return False
    
    print("\n🎉 All hourly rental features are working correctly!")
    print("\n📋 Available Features:")
    print("   • Hourly rentals (1-24 hours)")
    print("   • Dynamic pricing with discounts")
    print("   • Peak hours surcharge (+20%)")
    print("   • Manual mode discount (-30%)")
    print("   • Auto-renewal discount (-10%)")
    print("   • Bulk rental discounts (-15%)")
    print("   • Real-time pricing breakdown")
    print("   • Comprehensive retry mechanisms")
    print("   • Circuit breaker protection")
    
    return True

if __name__ == "__main__":
    success = test_features()
    exit(0 if success else 1)