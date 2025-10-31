#!/usr/bin/env python3
"""Fix using Render environment variables"""

import requests
import json

def update_render_database_url():
    """Instructions to update DATABASE_URL in Render"""
    
    print("🔧 Render DATABASE_URL Fix")
    print("=" * 40)
    
    print("\n📋 COPY THIS NEW DATABASE_URL TO RENDER:")
    print("=" * 40)
    
    # Session Pooler URL (IPv4 compatible)
    new_url = "postgresql://postgres.oegyaxxlzmogrtgmhrcy:ryskyx-8Padsa-timtabodh@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    
    print(new_url)
    
    print("\n📝 STEPS:")
    print("1. Go to your Render dashboard")
    print("2. Find the DATABASE_URL environment variable")
    print("3. Replace the current value with the URL above")
    print("4. Click 'Manual Deploy' to restart the service")
    
    print("\n🔍 KEY CHANGES:")
    print("- Using Session Pooler (aws-0-us-east-1.pooler.supabase.com)")
    print("- Port 6543 instead of 5432")
    print("- IPv4 compatible connection")
    
    return new_url

def test_after_update():
    """Test the connection after updating Render"""
    
    print("\n⏳ Wait 2-3 minutes after updating Render, then test:")
    print("=" * 50)
    
    print("\n1. Test health endpoint:")
    print("curl https://namaskahsms.onrender.com/system/health")
    
    print("\n2. Create admin user:")
    print("curl -X POST https://namaskahsms.onrender.com/setup/create-admin")
    
    print("\n3. Test login at:")
    print("https://namaskahsms.onrender.com/app")
    print("Email: admin@namaskah.app")
    print("Password: Namaskah@Admin2024")

def main():
    new_url = update_render_database_url()
    test_after_update()
    
    print("\n" + "=" * 50)
    print("🚨 ACTION REQUIRED:")
    print("Update DATABASE_URL in Render with the URL shown above!")
    print("=" * 50)

if __name__ == "__main__":
    main()