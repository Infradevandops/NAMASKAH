#!/usr/bin/env python3
"""Fix database connection issues"""

import os
import sys

def update_database_config():
    """Update database configuration for production"""
    
    # Check if we have environment variables set
    current_db_url = os.getenv('DATABASE_URL')
    print(f"Current DATABASE_URL: {current_db_url}")
    
    # Suggest fixes
    print("\n🔧 Database Connection Fixes:")
    print("1. Check database project status in your provider dashboard")
    print("2. Verify database is not paused or suspended")
    print("3. Check if IP restrictions are blocking Render.com")
    print("4. Verify DATABASE_URL environment variable in Render dashboard")
    
    # Provide correct format
    print("\n📋 Correct DATABASE_URL format:")
    print("postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].provider.co:5432/postgres")
    
    # Check network connectivity
    print("\n🌐 Testing network connectivity...")
    import subprocess
    try:
        result = subprocess.run(['ping', '-c', '1', 'db.PROJECT-REF.provider.co'], 
                              capture_output=True, text=True, timeout=10, check=False)
        if result.returncode == 0:
            print("✅ Host is reachable")
        else:
            print("❌ Host is not reachable")
            print("This indicates a network or DNS issue")
    except Exception as e:
        print(f"❌ Network test failed: {e}")

def create_sqlite_fallback():
    """Create SQLite fallback for emergency access"""
    print("\n🔄 Creating SQLite fallback...")
    
    # Set SQLite as fallback
    os.environ['DATABASE_URL'] = 'sqlite:///./emergency.db'
    
    try:
        # Import after setting environment
        sys.path.append('.')
        from app.core.database import SessionLocal, engine
        from app.models.user import User
        from app.utils.security import hash_password, generate_secure_id
        
        # Create tables
        from app.models.base import Base
        Base.metadata.create_all(bind=engine)
        
        # Create admin user
        db = SessionLocal()
        
        # Check if admin exists
        existing = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if existing:
            print("✅ Admin user already exists in SQLite")
            db.close()
            return True
        
        # Create admin
        admin = User(
            email="admin@namaskah.app",
            password_hash=hash_password("Namaskah@Admin2024"),
            credits=1000.0,
            free_verifications=10,
            is_admin=True,
            email_verified=True,
            referral_code=generate_secure_id("admin", 6)
        )
        
        db.add(admin)
        db.commit()
        db.close()
        
        print("✅ SQLite fallback created with admin user")
        return True
        
    except Exception as e:
        print(f"❌ SQLite fallback failed: {e}")
        return False

def main():
    print("🔧 Database Connection Fix")
    print("=" * 40)
    
    update_database_config()
    
    print("\n" + "=" * 40)
    print("🚨 IMMEDIATE ACTIONS NEEDED:")
    print("1. Go to Render.com dashboard")
    print("2. Check Environment Variables")
    print("3. Verify DATABASE_URL is correct")
    print("4. Check Supabase project status")
    print("5. Restart the Render service")
    
    # Offer SQLite fallback for local testing
    response = input("\nCreate SQLite fallback for local testing? (y/n): ")
    if response.lower() == 'y':
        create_sqlite_fallback()

if __name__ == "__main__":
    main()