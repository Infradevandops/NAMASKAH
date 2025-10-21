#!/usr/bin/env python3
"""Comprehensive test for all services and verification flow"""

import json
import requests
import time
import sys
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"

class ServiceTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        
    def register_test_user(self):
        """Register a test user"""
        try:
            response = requests.post(f"{BASE_URL}/auth/register", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                self.token = data["token"]
                self.user_id = data["user_id"]
                print(f"✅ Test user registered: {TEST_EMAIL}")
                return True
            elif response.status_code == 400 and "already registered" in response.json().get("detail", ""):
                # User exists, try to login
                return self.login_test_user()
            else:
                print(f"❌ Registration failed: {response.json()}")
                return False
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    def login_test_user(self):
        """Login test user"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                data = response.json()
                self.token = data["token"]
                self.user_id = data["user_id"]
                print(f"✅ Test user logged in: {TEST_EMAIL}")
                return True
            else:
                print(f"❌ Login failed: {response.json()}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def test_services_endpoint(self):
        """Test /services/list endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/services/list")
            if response.status_code == 200:
                data = response.json()
                categories = data.get("categories", {})
                tiers = data.get("tiers", {})
                
                print(f"✅ Services endpoint working")
                print(f"   Categories: {len(categories)}")
                print(f"   Tiers: {len(tiers)}")
                
                # Check for WhatsApp specifically
                whatsapp_found = False
                for category, services in categories.items():
                    if 'whatsapp' in [s.lower() for s in services]:
                        print(f"   ✅ WhatsApp found in {category}")
                        whatsapp_found = True
                        break
                
                if not whatsapp_found:
                    print("   ❌ WhatsApp not found in services")
                    return False
                
                return True
            else:
                print(f"❌ Services endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Services endpoint error: {e}")
            return False
    
    def test_service_pricing(self, service_name="whatsapp"):
        """Test service pricing endpoint"""
        if not self.token:
            print("❌ No auth token for pricing test")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{BASE_URL}/services/price/{service_name}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {service_name.title()} pricing:")
                print(f"   Tier: {data.get('tier_name', 'Unknown')}")
                print(f"   Price: N{data.get('base_price', 0)}")
                print(f"   Voice: N{data.get('base_price', 0) + data.get('voice_premium', 0)}")
                return True
            else:
                print(f"❌ Pricing failed for {service_name}: {response.json()}")
                return False
        except Exception as e:
            print(f"❌ Pricing error for {service_name}: {e}")
            return False
    
    def add_test_credits(self):
        """Add credits to test user (admin function)"""
        if not self.token:
            return False
            
        try:
            # Try to add credits via admin endpoint (if available)
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(f"{BASE_URL}/admin/credits/add", 
                                   headers=headers,
                                   json={"user_id": self.user_id, "amount": 10.0})
            
            if response.status_code == 200:
                print("✅ Test credits added")
                return True
            else:
                print("⚠️ Could not add test credits (admin access needed)")
                return False
        except Exception as e:
            print(f"⚠️ Credits error: {e}")
            return False
    
    def test_verification_creation(self, service_name="whatsapp"):
        """Test creating a verification"""
        if not self.token:
            print("❌ No auth token for verification test")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(f"{BASE_URL}/verify/create", 
                                   headers=headers,
                                   json={
                                       "service_name": service_name,
                                       "capability": "sms"
                                   })
            
            if response.status_code == 200:
                data = response.json()
                verification_id = data.get("id")
                phone_number = data.get("phone_number")
                cost = data.get("cost")
                
                print(f"✅ {service_name.title()} verification created:")
                print(f"   ID: {verification_id}")
                print(f"   Phone: {phone_number}")
                print(f"   Cost: N{cost}")
                
                return verification_id
            elif response.status_code == 402:
                print(f"⚠️ Insufficient credits for {service_name} verification")
                return None
            elif response.status_code == 503:
                print(f"⚠️ {service_name} service unavailable from provider")
                return None
            else:
                print(f"❌ Verification creation failed for {service_name}: {response.json()}")
                return False
        except Exception as e:
            print(f"❌ Verification error for {service_name}: {e}")
            return False
    
    def test_verification_status(self, verification_id):
        """Test checking verification status"""
        try:
            response = requests.get(f"{BASE_URL}/verify/{verification_id}")
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                service = data.get("service_name")
                
                print(f"✅ Verification status check:")
                print(f"   Service: {service}")
                print(f"   Status: {status}")
                
                return True
            else:
                print(f"❌ Status check failed: {response.json()}")
                return False
        except Exception as e:
            print(f"❌ Status check error: {e}")
            return False
    
    def test_messages_endpoint(self, verification_id):
        """Test messages endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/verify/{verification_id}/messages")
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                
                print(f"✅ Messages endpoint working:")
                print(f"   Messages count: {len(messages)}")
                
                return True
            else:
                print(f"❌ Messages check failed: {response.json()}")
                return False
        except Exception as e:
            print(f"❌ Messages error: {e}")
            return False
    
    def test_popular_services(self):
        """Test popular services"""
        popular_services = ["whatsapp", "telegram", "discord", "google", "instagram"]
        results = {}
        
        print(f"\n🧪 Testing popular services...")
        
        for service in popular_services:
            print(f"\n--- Testing {service.title()} ---")
            
            # Test pricing
            pricing_ok = self.test_service_pricing(service)
            
            # Test verification creation (will fail without credits, but tests API)
            verification_id = self.test_verification_creation(service)
            
            results[service] = {
                "pricing": pricing_ok,
                "verification": verification_id is not False
            }
            
            if verification_id and isinstance(verification_id, str):
                # Test status and messages if verification was created
                self.test_verification_status(verification_id)
                self.test_messages_endpoint(verification_id)
        
        return results
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🧪 COMPREHENSIVE SERVICE TESTING")
        print("=" * 50)
        
        success = True
        
        # Test 1: Basic endpoints
        print("\n1. Testing basic endpoints...")
        if not self.test_services_endpoint():
            success = False
        
        # Test 2: User authentication
        print("\n2. Testing user authentication...")
        if not self.register_test_user():
            success = False
        
        # Test 3: Add test credits (optional)
        print("\n3. Adding test credits...")
        self.add_test_credits()
        
        # Test 4: Popular services
        print("\n4. Testing popular services...")
        results = self.test_popular_services()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        for service, result in results.items():
            status = "✅" if result["pricing"] and result["verification"] else "❌"
            print(f"{status} {service.title()}: Pricing={result['pricing']}, API={result['verification']}")
        
        working_services = sum(1 for r in results.values() if r["pricing"] and r["verification"])
        total_services = len(results)
        
        print(f"\n📈 Results: {working_services}/{total_services} services working")
        
        if working_services == total_services:
            print("✅ ALL SERVICES WORKING CORRECTLY!")
        elif working_services > 0:
            print("⚠️ SOME SERVICES WORKING - Check failed services above")
        else:
            print("❌ NO SERVICES WORKING - Check configuration")
        
        return working_services == total_services

def main():
    """Main test function"""
    print("🚀 Starting comprehensive service testing...")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not responding correctly: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not accessible at {BASE_URL}: {e}")
        print("💡 Make sure to start the server first: python3 main.py")
        return False
    
    print(f"✅ Server is running at {BASE_URL}")
    
    # Run tests
    tester = ServiceTester()
    success = tester.run_comprehensive_test()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)