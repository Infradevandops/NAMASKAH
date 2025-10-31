#!/usr/bin/env python3
"""Emergency production fix for login issues"""

import os
import requests
import json

def test_login():
    """Test admin login"""
    url = "https://namaskahsms.onrender.com/auth/login"
    data = {
        "email": "admin@namaskah.app",
        "password": "Namaskah@Admin2024"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Login response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login successful!")
            print(f"Token: {result.get('access_token', 'No token')[:20]}...")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

def create_admin():
    """Create admin user via setup endpoint"""
    url = "https://namaskahsms.onrender.com/setup/create-admin"
    
    try:
        response = requests.post(url, timeout=10)
        print(f"Admin creation response: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Admin creation successful!")
            return True
        else:
            print("❌ Admin creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Admin creation error: {e}")
        return False

def check_health():
    """Check system health"""
    url = "https://namaskahsms.onrender.com/system/health"
    
    try:
        response = requests.get(url, timeout=10)
        health = response.json()
        
        print(f"System status: {health.get('status')}")
        
        db_status = health.get('services', {}).get('database', {})
        print(f"Database status: {db_status.get('status')}")
        
        if db_status.get('error'):
            print(f"Database error: {db_status['error']}")
            
        return health.get('status') == 'healthy'
        
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def main():
    print("🔧 Emergency Production Fix")
    print("=" * 40)
    
    print("\n1. Checking system health...")
    healthy = check_health()
    
    if not healthy:
        print("\n2. System unhealthy - database issues detected")
        print("   This requires infrastructure-level fixes")
        return False
    
    print("\n2. Testing admin login...")
    login_works = test_login()
    
    if not login_works:
        print("\n3. Creating admin user...")
        admin_created = create_admin()
        
        if admin_created:
            print("\n4. Testing login again...")
            login_works = test_login()
    
    if login_works:
        print("\n✅ Production fix successful!")
        print("Admin can now login at: https://namaskahsms.onrender.com/app")
        return True
    else:
        print("\n❌ Production fix failed")
        print("Manual intervention required")
        return False

if __name__ == "__main__":
    main()