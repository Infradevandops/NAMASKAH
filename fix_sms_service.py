#!/usr/bin/env python3
"""
Quick fix for SMS service integration
"""
import asyncio
import sys
import os
sys.path.append('.')

async def test_services():
    """Test the services endpoint functionality"""
    try:
        from app.services.textverified_service import TextVerifiedService
        
        print("🔧 Testing TextVerified Service...")
        service = TextVerifiedService()
        result = await service.get_services()
        
        print("✅ Services Result:")
        print(result)
        
        if "services" in result:
            print(f"📱 Found {len(result['services'])} services")
            for svc in result['services'][:3]:  # Show first 3
                print(f"  - {svc['name']}: ${svc['price']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_environment():
    """Check environment configuration"""
    print("🔍 Checking Environment Configuration...")
    
    # Check critical environment variables
    env_vars = [
        'DATABASE_URL',
        'SECRET_KEY', 
        'JWT_SECRET_KEY',
        'TEXTVERIFIED_API_KEY',
        'PAYSTACK_SECRET_KEY'
    ]
    
    for var in env_vars:
        value = os.getenv(var, 'NOT_SET')
        if value == 'NOT_SET':
            print(f"⚠️  {var}: Not configured")
        elif 'your_' in value or 'change_me' in value:
            print(f"⚠️  {var}: Placeholder value")
        else:
            print(f"✅ {var}: Configured")

async def main():
    """Main test function"""
    print("🚀 Namaskah SMS - Service Fix Test")
    print("=" * 40)
    
    # Check environment
    check_environment()
    print()
    
    # Test services
    success = await test_services()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ SMS Service test completed successfully")
        print("📝 Next steps:")
        print("   1. Deploy changes to Render")
        print("   2. Test /verify/services endpoint")
        print("   3. Create production admin user")
    else:
        print("❌ SMS Service test failed")
        print("📝 Check configuration and try again")

if __name__ == "__main__":
    asyncio.run(main())