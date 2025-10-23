#!/usr/bin/env python3
"""
Simple dashboard health check script
Tests core functionality that should be working
"""

import requests
import json
import sys

def test_endpoint(url, description, expected_status=200):
    """Test an endpoint and return result"""
    try:
        response = requests.get(url, timeout=5)
        status = "✅ PASS" if response.status_code == expected_status else f"❌ FAIL ({response.status_code})"
        print(f"{status} - {description}")
        return response.status_code == expected_status
    except Exception as e:
        print(f"❌ ERROR - {description}: {str(e)}")
        return False

def main():
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Namaskah Dashboard Core Functionality")
    print("=" * 50)
    
    tests = [
        (f"{base_url}/health", "Health check endpoint"),
        (f"{base_url}/", "Landing page"),
        (f"{base_url}/app", "Main dashboard"),
        (f"{base_url}/admin", "Admin dashboard"),
        (f"{base_url}/services/list", "Services list API"),
        (f"{base_url}/auth/google/config", "Google OAuth config"),
        (f"{base_url}/docs", "API documentation"),
    ]
    
    passed = 0
    total = len(tests)
    
    for url, description in tests:
        if test_endpoint(url, description):
            passed += 1
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All core functionality is working!")
        return 0
    else:
        print("⚠️  Some issues found - check the failing endpoints")
        return 1

if __name__ == "__main__":
    sys.exit(main())