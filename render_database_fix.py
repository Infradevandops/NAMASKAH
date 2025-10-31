#!/usr/bin/env python3
"""Quick fix for Render database connection"""

import requests
import json

def test_connection():
    """Test database connection via health endpoint"""
    try:
        response = requests.get("https://namaskahsms.onrender.com/system/health", timeout=10)
        health = response.json()
        
        print(f"System Status: {health.get('status')}")
        
        db_status = health.get('services', {}).get('database', {})
        print(f"Database Status: {db_status.get('status')}")
        
        if db_status.get('error'):
            print(f"Error: {db_status['error']}")
            
        return db_status.get('status') == 'healthy'
        
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def create_admin():
    """Create admin user via setup endpoint"""
    try:
        response = requests.post("https://namaskahsms.onrender.com/setup/create-admin", timeout=15)
        print(f"Admin creation: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Result: {result}")
            return True
        else:
            print(f"Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Admin creation failed: {e}")
        return False

def test_login():
    """Test admin login"""
    try:
        response = requests.post(
            "https://namaskahsms.onrender.com/auth/login",
            json={"email": "admin@namaskah.app", "password": "Namaskah@Admin2024"},
            timeout=10
        )
        
        print(f"Login Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login successful!")
            return True
        else:
            print(f"Login failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Login test failed: {e}")
        return False

def main():
    print("🔧 Render Database Fix")
    print("=" * 30)
    
    print("\n1. Testing database connection...")
    db_healthy = test_connection()
    
    if db_healthy:
        print("\n2. Database is healthy! Testing login...")
        login_works = test_login()
        
        if not login_works:
            print("\n3. Creating admin user...")
            create_admin()
            print("\n4. Testing login again...")
            test_login()
    else:
        print("\n2. Database unhealthy. Trying admin creation anyway...")
        create_admin()

if __name__ == "__main__":
    main()