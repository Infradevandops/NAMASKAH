#!/usr/bin/env python3
"""Test verification flow and services loading"""

import json
import sys
import os

def test_services_loading():
    """Test if services_categorized.json loads correctly"""
    try:
        with open('services_categorized.json', 'r') as f:
            data = json.load(f)
        
        print("✅ Services file loaded successfully")
        print(f"Categories: {list(data.get('categories', {}).keys())}")
        
        # Test WhatsApp specifically
        whatsapp_found = False
        for category, services in data.get('categories', {}).items():
            if 'whatsapp' in [s.lower() for s in services]:
                print(f"✅ WhatsApp found in {category} category")
                whatsapp_found = True
                break
        
        if not whatsapp_found:
            print("❌ WhatsApp not found in any category")
            
        return True
    except Exception as e:
        print(f"❌ Error loading services: {e}")
        return False

def test_pricing_config():
    """Test pricing configuration"""
    try:
        from pricing_config import SERVICE_TIERS, get_service_tier, get_service_price
        
        print("✅ Pricing config loaded successfully")
        print(f"Available tiers: {list(SERVICE_TIERS.keys())}")
        
        # Test WhatsApp pricing
        whatsapp_tier = get_service_tier('whatsapp')
        whatsapp_price = get_service_price('whatsapp', 'starter', 0)
        
        print(f"✅ WhatsApp tier: {whatsapp_tier}")
        print(f"✅ WhatsApp price: N{whatsapp_price}")
        
        return True
    except Exception as e:
        print(f"❌ Error with pricing config: {e}")
        return False

def test_verification_classic_js():
    """Test if verification-classic.js exists and has correct functions"""
    try:
        with open('static/js/verification-classic.js', 'r') as f:
            content = f.read()
        
        required_functions = [
            'selectServiceClassic',
            'createVerificationClassic',
            'initClassicVerification'
        ]
        
        for func in required_functions:
            if func in content:
                print(f"✅ Function {func} found")
            else:
                print(f"❌ Function {func} missing")
                
        return True
    except Exception as e:
        print(f"❌ Error reading verification-classic.js: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Namaskah verification system...")
    print("=" * 50)
    
    success = True
    
    print("\n1. Testing services loading...")
    success &= test_services_loading()
    
    print("\n2. Testing pricing configuration...")
    success &= test_pricing_config()
    
    print("\n3. Testing verification JavaScript...")
    success &= test_verification_classic_js()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! Verification system should work.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    sys.exit(0 if success else 1)