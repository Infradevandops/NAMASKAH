#!/usr/bin/env python3
"""Diagnose production authentication issues"""

import requests
import json

def test_api_endpoints():
    """Test production API endpoints"""
    base_url = "https://namaskah.onrender.com"
    
    print("🔍 Testing Production API Endpoints")
    print("=" * 50)
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Root endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Service: {data.get('service')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Status: {data.get('status')}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/system/health")
        print(f"✅ Health endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status')}")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
    
    # Test registration
    print("\n📝 Testing Registration...")
    try:
        test_email = "test@example.com"
        test_password = "TestPassword123"
        
        response = requests.post(f"{base_url}/auth/register", json={
            "email": test_email,
            "password": test_password
        })
        
        print(f"Registration response: {response.status_code}")
        if response.status_code != 200:
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}")
        else:
            print("✅ Registration successful")
            
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
    
    # Test login with admin credentials
    print("\n🔐 Testing Admin Login...")
    try:
        response = requests.post(f"{base_url}/auth/login", json={
            "email": "admin@namaskah.app",
            "password": "Namaskah@Admin2024"
        })
        
        print(f"Admin login response: {response.status_code}")
        if response.status_code == 200:
            print("✅ Admin login successful")
            data = response.json()
            if 'access_token' in data:
                print("✅ Token received")
            if 'user' in data:
                user = data['user']
                print(f"   Email: {user.get('email')}")
                print(f"   Admin: {user.get('is_admin')}")
        else:
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}")
                
    except Exception as e:
        print(f"❌ Admin login test failed: {e}")
    
    # Test docs endpoint
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"\n📚 Docs endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Docs endpoint failed: {e}")

def check_database_status():
    """Check database status via health endpoint"""
    try:
        response = requests.get("https://namaskah.onrender.com/system/health")
        if response.status_code == 200:
            data = response.json()
            services = data.get('services', {})
            db_status = services.get('database', {})
            
            print(f"\n🗄️ Database Status: {db_status.get('status', 'unknown')}")
            if 'error' in db_status:
                print(f"   Error: {db_status['error']}")
            
            return db_status.get('status') == 'healthy'
    except Exception as e:
        print(f"❌ Could not check database status: {e}")
    
    return False

def main():
    print("🔍 Production Diagnosis Report")
    print("=" * 50)
    
    # Check if database is healthy
    db_healthy = check_database_status()
    
    # Test API endpoints
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("📋 Diagnosis Summary:")
    print(f"   Database: {'✅ Healthy' if db_healthy else '❌ Issues detected'}")
    print("   API: Check results above")
    
    if not db_healthy:
        print("\n🔧 Recommended Actions:")
        print("   1. Check Supabase database connection")
        print("   2. Verify DATABASE_URL environment variable")
        print("   3. Run database migrations")
        print("   4. Create admin user manually")

if __name__ == "__main__":
    main()