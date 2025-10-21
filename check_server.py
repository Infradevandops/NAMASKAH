#!/usr/bin/env python3
"""Quick server health check"""

import requests
import sys

def check_server():
    """Check if server is running and healthy"""
    try:
        # Check health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is healthy")
            print(f"   Status: {data.get('status')}")
            print(f"   Service: {data.get('service')}")
            print(f"   Database: {data.get('database')}")
            return True
        else:
            print(f"❌ Server unhealthy: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server not running on localhost:8000")
        print("💡 Start server with: python3 main.py")
        return False
    except Exception as e:
        print(f"❌ Server check failed: {e}")
        return False

if __name__ == "__main__":
    success = check_server()
    sys.exit(0 if success else 1)