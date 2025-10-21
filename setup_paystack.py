#!/usr/bin/env python3
"""
Paystack Configuration Helper
Sets up Paystack test keys for immediate testing
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

def setup_paystack_test():
    """Setup Paystack test keys for immediate functionality"""
    
    print("🔧 Paystack Configuration Setup")
    print("=" * 40)
    
    # Check current configuration
    secret_key = os.getenv("PAYSTACK_SECRET_KEY")
    public_key = os.getenv("PAYSTACK_PUBLIC_KEY")
    
    if secret_key and secret_key.startswith("sk_"):
        print(f"✅ Secret Key: {secret_key[:15]}...")
        secret_configured = True
    else:
        print("❌ Secret Key: Not configured")
        secret_configured = False
    
    if public_key and public_key.startswith("pk_"):
        print(f"✅ Public Key: {public_key[:15]}...")
        public_configured = True
    else:
        print("❌ Public Key: Not configured")
        public_configured = False
    
    if secret_configured and public_configured:
        print("\n🎉 Paystack is already configured!")
        return True
    
    print("\n📝 To configure Paystack:")
    print("1. Get your keys from: https://dashboard.paystack.com/#/settings/developers")
    print("2. Update .env file with your keys:")
    print("   PAYSTACK_SECRET_KEY=sk_test_your_key_here")
    print("   PAYSTACK_PUBLIC_KEY=pk_test_your_key_here")
    
    # For demo purposes, set up test keys
    print("\n🧪 Setting up demo test keys...")
    
    # Update .env file with demo keys
    env_content = """# Environment Configuration
JWT_SECRET_KEY=namaskah-production-secret-2024-change-me
DATABASE_URL=sqlite:///./namaskah.db

# TextVerified API (Demo keys - replace with real ones)
TEXTVERIFIED_API_KEY=demo-key-replace-with-real
TEXTVERIFIED_EMAIL=demo@example.com

# Paystack Configuration (TEST KEYS - REPLACE WITH REAL ONES)
PAYSTACK_SECRET_KEY=sk_test_demo_key_for_testing_replace_with_real
PAYSTACK_PUBLIC_KEY=pk_test_demo_key_for_testing_replace_with_real

# Email Configuration (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@namaskah.app

# Base URL
BASE_URL=http://localhost:8000

# Security
CORS_ORIGINS=*
ENVIRONMENT=development"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Demo keys configured in .env")
    print("\n⚠️  IMPORTANT: Replace with real Paystack keys for production!")
    
    return False

def test_paystack_connection():
    """Test Paystack API connection"""
    import requests
    
    secret_key = os.getenv("PAYSTACK_SECRET_KEY")
    
    if not secret_key or not secret_key.startswith("sk_"):
        print("❌ Cannot test - no valid secret key")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {secret_key}"}
        response = requests.get("https://api.paystack.co/bank", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Paystack API: Connected successfully")
            return True
        else:
            print(f"❌ Paystack API: Error {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Paystack API: Connection failed - {e}")
        return False

if __name__ == "__main__":
    configured = setup_paystack_test()
    
    if configured:
        print("\n🧪 Testing Paystack connection...")
        test_paystack_connection()
    
    print("\n🚀 Next steps:")
    print("1. Get real Paystack keys from dashboard")
    print("2. Update .env with your keys")
    print("3. Restart the server")
    print("4. Test payment functionality")