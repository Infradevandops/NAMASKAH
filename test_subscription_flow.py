#!/usr/bin/env python3
"""Test subscription flow end-to-end"""

import requests
import json

BASE_URL = "http://localhost:8000"
TEST_EMAIL = f"test_sub_{int(__import__('time').time())}@test.com"
TEST_PASSWORD = "Test123!"

def test_flow():
    print("\n" + "="*80)
    print("SUBSCRIPTION FLOW TEST")
    print("="*80)
    
    # 1. Register
    print("\n1️⃣ Testing Registration...")
    res = requests.post(f"{BASE_URL}/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    print(f"Status: {res.status_code}")
    if res.status_code != 200:
        print(f"❌ Registration failed: {res.text}")
        return
    
    data = res.json()
    token = data.get("token")
    print(f"✅ Registered: {TEST_EMAIL}")
    print(f"Credits: N{data.get('credits')}")
    print(f"Free verifications: {data.get('free_verifications')}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Check current plan (should be Starter by default)
    print("\n2️⃣ Testing Current Plan...")
    res = requests.get(f"{BASE_URL}/subscription/current", headers=headers)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        plan = res.json()
        print(f"✅ Current plan: {plan.get('name')}")
        print(f"Features: {plan.get('features')}")
    else:
        print(f"❌ Failed: {res.text}")
    
    # 3. Get available plans
    print("\n3️⃣ Testing Available Plans...")
    res = requests.get(f"{BASE_URL}/subscription/plans")
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        plans = res.json().get('plans', [])
        print(f"✅ Available plans: {len(plans)}")
        for p in plans:
            print(f"  - {p['name']}: ${p['price_usd']} ({p['duration']}) - {p['discount']} discount")
    else:
        print(f"❌ Failed: {res.text}")
    
    # 4. Try to subscribe without credits
    print("\n4️⃣ Testing Subscribe Without Credits...")
    res = requests.post(f"{BASE_URL}/subscription/subscribe", 
                       headers=headers,
                       json={"plan": "pro"})
    print(f"Status: {res.status_code}")
    if res.status_code == 402:
        print(f"✅ Correctly blocked: {res.json().get('detail')}")
    else:
        print(f"⚠️ Unexpected: {res.text}")
    
    # 5. Add credits manually (simulate payment)
    print("\n5️⃣ Adding Credits (Admin)...")
    # Login as admin
    admin_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@namaskah.app",
        "password": "Admin@2024!"
    })
    if admin_res.status_code == 200:
        admin_token = admin_res.json().get("token")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get user ID
        me_res = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        user_id = me_res.json().get("id")
        
        # Add credits
        add_res = requests.post(f"{BASE_URL}/admin/credits/add",
                               headers=admin_headers,
                               json={"user_id": user_id, "amount": 100.0})
        if add_res.status_code == 200:
            print(f"✅ Added N100 credits")
        else:
            print(f"❌ Failed to add credits: {add_res.text}")
    
    # 6. Subscribe to Pro plan
    print("\n6️⃣ Testing Subscribe to Pro...")
    res = requests.post(f"{BASE_URL}/subscription/subscribe",
                       headers=headers,
                       json={"plan": "pro"})
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"✅ Subscribed to Pro!")
        print(f"Duration: {data.get('duration')}")
        print(f"Expires: {data.get('expires_at')}")
        print(f"Remaining credits: N{data.get('remaining_credits')}")
    else:
        print(f"❌ Failed: {res.text}")
        return
    
    # 7. Test area code selection (Pro feature)
    print("\n7️⃣ Testing Area Code Selection (Pro)...")
    res = requests.post(f"{BASE_URL}/verify/create",
                       headers=headers,
                       json={
                           "service_name": "telegram",
                           "capability": "sms",
                           "area_code": "212"
                       })
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"✅ Verification created with area code!")
        print(f"Phone: {data.get('phone_number')}")
        print(f"Cost: N{data.get('cost')}")
        
        # Cancel it
        requests.delete(f"{BASE_URL}/verify/{data.get('id')}", headers=headers)
    else:
        print(f"❌ Failed: {res.text}")
    
    # 8. Test carrier selection (should fail - Pro doesn't have carrier)
    print("\n8️⃣ Testing Carrier Selection on Pro (should fail)...")
    res = requests.post(f"{BASE_URL}/verify/create",
                       headers=headers,
                       json={
                           "service_name": "telegram",
                           "capability": "sms",
                           "carrier": "verizon"
                       })
    print(f"Status: {res.status_code}")
    if res.status_code == 403:
        print(f"✅ Correctly blocked: {res.json().get('detail')}")
    else:
        print(f"⚠️ Unexpected: {res.text}")
    
    # 9. Upgrade to Turbo
    print("\n9️⃣ Testing Upgrade to Turbo...")
    res = requests.post(f"{BASE_URL}/subscription/subscribe",
                       headers=headers,
                       json={"plan": "turbo"})
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"✅ Upgraded to Turbo!")
        print(f"Duration: {data.get('duration')}")
        print(f"Expires: {data.get('expires_at')}")
    else:
        print(f"❌ Failed: {res.text}")
    
    # 10. Test carrier selection (should work now)
    print("\n🔟 Testing Carrier Selection on Turbo...")
    res = requests.post(f"{BASE_URL}/verify/create",
                       headers=headers,
                       json={
                           "service_name": "telegram",
                           "capability": "sms",
                           "area_code": "310",
                           "carrier": "verizon"
                       })
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"✅ Verification created with area code + carrier!")
        print(f"Phone: {data.get('phone_number')}")
        print(f"Cost: N{data.get('cost')} (35% discount applied)")
        
        # Cancel it
        requests.delete(f"{BASE_URL}/verify/{data.get('id')}", headers=headers)
    else:
        print(f"❌ Failed: {res.text}")
    
    # 11. Test rental with filters
    print("\n1️⃣1️⃣ Testing Rental with Filters (Turbo)...")
    res = requests.post(f"{BASE_URL}/rentals/create",
                       headers=headers,
                       json={
                           "service_name": "whatsapp",
                           "duration_hours": 168,
                           "mode": "always_ready",
                           "area_code": "415",
                           "carrier": "tmobile"
                       })
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"✅ Rental created with filters!")
        print(f"Phone: {data.get('phone_number')}")
        print(f"Cost: N{data.get('cost')}")
    else:
        print(f"❌ Failed: {res.text}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    test_flow()
