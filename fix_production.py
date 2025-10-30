#!/usr/bin/env python3
"""
Emergency Production Fix Script
Diagnoses and fixes critical production issues
"""
import os
import requests
import json
from datetime import datetime

def check_render_service():
    """Check Render service status"""
    try:
        response = requests.get("https://namaskahsms.onrender.com/system/health", timeout=10)
        print(f"✅ Service responding: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Service down: {e}")
        return False

def check_database_env():
    """Check if DATABASE_URL is properly set"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not set")
        return False
    
    if 'postgresql://' in db_url:
        print(f"✅ PostgreSQL URL configured: {db_url[:50]}...")
        return True
    else:
        print(f"⚠️ Non-PostgreSQL URL: {db_url}")
        return False

def main():
    print("🔍 PRODUCTION DIAGNOSIS")
    print("=" * 50)
    
    print("\n1. Checking Render Service...")
    service_ok = check_render_service()
    
    print("\n2. Checking Database Configuration...")
    db_ok = check_database_env()
    
    print("\n3. Diagnosis Summary:")
    if not service_ok:
        print("❌ CRITICAL: Production service is completely down")
        print("   - 503 Service Unavailable errors")
        print("   - Database connection likely failed")
        print("   - Service won't start due to DB issues")
    
    if not db_ok:
        print("❌ CRITICAL: Database configuration issues")
        print("   - DATABASE_URL may be incorrect")
        print("   - PostgreSQL connection failing")
    
    print("\n4. Required Actions:")
    print("   1. Check Render dashboard for database status")
    print("   2. Verify DATABASE_URL environment variable")
    print("   3. Restart Render service after DB fix")
    print("   4. Run /setup/create-admin after service recovery")
    
    print(f"\n🕐 Diagnosis completed at {datetime.now()}")

if __name__ == "__main__":
    main()