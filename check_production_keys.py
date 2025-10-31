#!/usr/bin/env python3
"""Check production API keys status"""

import os
import requests

def check_keys():
    """Check current API key status."""
    
    print("🔧 Production API Key Status")
    print("=" * 40)
    
    # Check environment variables
    keys = {
        'TEXTVERIFIED_API_KEY': os.getenv('TEXTVERIFIED_API_KEY', 'NOT_SET'),
        'PAYSTACK_SECRET_KEY': os.getenv('PAYSTACK_SECRET_KEY', 'NOT_SET'),
        'PAYSTACK_PUBLIC_KEY': os.getenv('PAYSTACK_PUBLIC_KEY', 'NOT_SET'),
        'DATABASE_URL': os.getenv('DATABASE_URL', 'NOT_SET')
    }
    
    for key, value in keys.items():
        if value == 'NOT_SET':
            print(f"❌ {key}: Not set")
        elif 'test' in value.lower() or 'development' in value.lower():
            print(f"⚠️  {key}: Using test key")
        else:
            print(f"✅ {key}: Production key set")
    
    print("\n📝 Required for Production:")
    print("1. TextVerified API Key (real account)")
    print("2. Paystack Live Keys (sk_live_... and pk_live_...)")
    print("3. Update Render environment variables")
    
    print("\n🔗 Get API Keys:")
    print("• TextVerified: https://www.textverified.com/")
    print("• Paystack: https://dashboard.paystack.com/")

if __name__ == "__main__":
    check_keys()