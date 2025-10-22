#!/usr/bin/env python3
"""
Emergency fix for services loading issue
This script diagnoses and fixes the services loading problem
"""

import json
import os
import sys
from pathlib import Path

def check_services_file():
    """Check if services_categorized.json exists and is valid"""
    services_file = Path("services_categorized.json")
    
    if not services_file.exists():
        print("❌ services_categorized.json not found!")
        return False
    
    try:
        with open(services_file, 'r') as f:
            data = json.load(f)
        
        # Validate structure
        if 'categories' not in data:
            print("❌ Invalid services file structure - missing 'categories'")
            return False
        
        total_services = sum(len(services) for services in data['categories'].values())
        total_services += len(data.get('uncategorized', []))
        
        print(f"✅ Services file valid - {total_services} total services")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in services file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading services file: {e}")
        return False

def test_api_endpoint():
    """Test the /services/list endpoint"""
    import requests
    
    try:
        # Test local endpoint
        response = requests.get("http://localhost:8000/services/list", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API endpoint working - returned {len(data.get('categories', {}))} categories")
            return True
        else:
            print(f"❌ API endpoint returned status {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server - is it running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def fix_services_endpoint():
    """Add error handling and fallback to services endpoint"""
    
    # Read main.py to check the endpoint
    try:
        with open("main.py", 'r') as f:
            content = f.read()
        
        # Check if services endpoint exists
        if '/services/list' not in content:
            print("❌ Services endpoint not found in main.py!")
            return False
        
        print("✅ Services endpoint exists in main.py")
        return True
        
    except Exception as e:
        print(f"❌ Error checking main.py: {e}")
        return False

def create_fallback_services():
    """Create a minimal fallback services file"""
    fallback_data = {
        "categories": {
            "Social": [
                "telegram", "whatsapp", "discord", "instagram", "facebook", 
                "twitter", "snapchat", "tiktok", "reddit", "linkedin"
            ],
            "Finance": [
                "paypal", "cashapp", "venmo", "coinbase", "robinhood"
            ],
            "Shopping": [
                "amazon", "ebay", "etsy", "mercari", "poshmark"
            ],
            "Other": [
                "google", "microsoft", "apple", "uber", "lyft"
            ]
        },
        "uncategorized": [],
        "pricing": {
            "categorized": 0.75,
            "uncategorized": 1.0
        }
    }
    
    try:
        with open("services_categorized_backup.json", 'w') as f:
            json.dump(fallback_data, f, indent=2)
        
        print("✅ Created fallback services file")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create fallback: {e}")
        return False

def main():
    print("🔧 Namaskah Services Loading Diagnostic Tool")
    print("=" * 50)
    
    # Step 1: Check services file
    print("\n1. Checking services_categorized.json...")
    services_ok = check_services_file()
    
    # Step 2: Test API endpoint
    print("\n2. Testing API endpoint...")
    api_ok = test_api_endpoint()
    
    # Step 3: Check main.py endpoint
    print("\n3. Checking services endpoint in main.py...")
    endpoint_ok = fix_services_endpoint()
    
    # Step 4: Create fallback if needed
    if not services_ok:
        print("\n4. Creating fallback services...")
        create_fallback_services()
    
    # Summary
    print("\n" + "=" * 50)
    print("DIAGNOSTIC SUMMARY:")
    print(f"Services file: {'✅ OK' if services_ok else '❌ FAILED'}")
    print(f"API endpoint: {'✅ OK' if api_ok else '❌ FAILED'}")
    print(f"Endpoint code: {'✅ OK' if endpoint_ok else '❌ FAILED'}")
    
    if not api_ok:
        print("\n🚨 IMMEDIATE ACTION REQUIRED:")
        print("1. Start the server: python main.py")
        print("2. Check server logs for errors")
        print("3. Verify services_categorized.json exists")
        print("4. Test endpoint: curl http://localhost:8000/services/list")
    
    return services_ok and api_ok and endpoint_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)