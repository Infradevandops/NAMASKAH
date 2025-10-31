#!/usr/bin/env python3
"""Create production admin via API - Best Practice Approach"""

import requests
import json
import time

def create_admin_via_direct_db():
    """Create admin by directly calling the production API"""
    
    base_url = "https://namaskah.onrender.com"
    
    print("🔧 Creating Production Admin User")
    print("=" * 40)
    
    # First, try to register the admin user
    admin_data = {
        "email": "admin@namaskah.app",
        "password": "Namaskah@Admin2024"
    }
    
    print("1. Attempting to register admin user...")
    try:
        response = requests.post(f"{base_url}/auth/register", json=admin_data)
        
        if response.status_code == 201:
            print("✅ Admin user registered successfully")
            data = response.json()
            token = data.get('access_token')
            user = data.get('user', {})
            
            print(f"   Email: {user.get('email')}")
            print(f"   User ID: {user.get('id')}")
            print(f"   Token: {token[:20]}..." if token else "   No token")
            
            return True
            
        elif response.status_code == 400:
            error_data = response.json()
            if "already registered" in error_data.get('detail', '').lower():
                print("ℹ️ Admin user already exists, trying login...")
                return test_admin_login()
            else:
                print(f"❌ Registration failed: {error_data.get('detail')}")
                
        else:
            print(f"❌ Registration failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except (ValueError, KeyError):
                print(f"   Raw response: {response.text[:200]}")
                
    except Exception as e:
        print(f"❌ Registration request failed: {e}")
    
    return False

def test_admin_login():
    """Test admin login"""
    
    base_url = "https://namaskah.onrender.com"
    
    print("2. Testing admin login...")
    try:
        response = requests.post(f"{base_url}/auth/login", json={
            "email": "admin@namaskah.app", 
            "password": "Namaskah@Admin2024"
        })
        
        if response.status_code == 200:
            print("✅ Admin login successful")
            data = response.json()
            user = data.get('user', {})
            
            print(f"   Email: {user.get('email')}")
            print(f"   Admin: {user.get('is_admin', False)}")
            print(f"   Credits: {user.get('credits', 0)}")
            
            return True
        else:
            print(f"❌ Login failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except (ValueError, KeyError):
                print(f"   Raw response: {response.text[:200]}")
                
    except Exception as e:
        print(f"❌ Login request failed: {e}")
    
    return False

def wait_for_healthy_database():
    """Wait for database to become healthy"""
    
    base_url = "https://namaskah.onrender.com"
    max_attempts = 10
    
    print("🔍 Waiting for database to become healthy...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{base_url}/system/health")
            if response.status_code == 200:
                data = response.json()
                db_status = data.get('services', {}).get('database', {}).get('status')
                
                if db_status == 'healthy':
                    print("✅ Database is healthy")
                    return True
                else:
                    print(f"   Attempt {attempt + 1}: Database status = {db_status}")
            
            if attempt < max_attempts - 1:
                time.sleep(5)  # Wait 5 seconds between attempts
                
        except Exception as e:
            print(f"   Attempt {attempt + 1}: Health check failed - {e}")
            if attempt < max_attempts - 1:
                time.sleep(5)
    
    print("⚠️ Database may still be unhealthy, proceeding anyway...")
    return False

def main():
    """Main function"""
    
    print("🚀 Production Admin Setup")
    print("=" * 50)
    
    # Wait for database to be healthy
    wait_for_healthy_database()
    
    # Try to create admin user
    success = create_admin_via_direct_db()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Production admin setup complete!")
        print("\n🔐 Login Credentials:")
        print("   URL: https://namaskah.onrender.com/")
        print("   Email: admin@namaskah.app")
        print("   Password: Namaskah@Admin2024")
        print("\n📝 Next Steps:")
        print("   1. Login to verify access")
        print("   2. Test user registration")
        print("   3. Check admin panel functionality")
    else:
        print("\n" + "=" * 50)
        print("❌ Admin setup failed")
        print("\n🔧 Troubleshooting:")
        print("   1. Check database health")
        print("   2. Verify API endpoints are working")
        print("   3. Check server logs for errors")

if __name__ == "__main__":
    main()