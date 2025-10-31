#!/usr/bin/env python3
"""Fix production admin login issue"""

import os
import sys
sys.path.append('.')

# Set production environment
os.environ['ENVIRONMENT'] = 'production'

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.utils.security import hash_password, generate_secure_id

def fix_admin_login():
    """Fix admin login in production database"""
    
    # Get production database URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("Set it with: export DATABASE_URL='your_supabase_connection_string'")
        return False
    
    print(f"🔗 Connecting to: {database_url[:50]}...")
    
    try:
        # Create engine and session
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Test connection
        db.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        
        # Check if admin exists
        existing_admin = db.query(User).filter(User.email == "admin@namaskah.app").first()
        
        if existing_admin:
            print(f"👤 Found existing admin: {existing_admin.email}")
            print(f"   ID: {existing_admin.id}")
            print(f"   Is Admin: {existing_admin.is_admin}")
            print(f"   Email Verified: {existing_admin.email_verified}")
            
            # Update password to ensure it's correct
            existing_admin.password_hash = hash_password("Namaskah@Admin2024")
            existing_admin.is_admin = True
            existing_admin.email_verified = True
            db.commit()
            print("🔄 Updated admin password and permissions")
            
        else:
            print("👤 Creating new admin user...")
            
            # Create admin user
            admin_user = User(
                email="admin@namaskah.app",
                password_hash=hash_password("Namaskah@Admin2024"),
                credits=1000.0,
                free_verifications=10.0,
                is_admin=True,
                email_verified=True,
                referral_code=generate_secure_id("admin", 6)
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"✅ Created admin user with ID: {admin_user.id}")
        
        # Verify login credentials
        from app.utils.security import verify_password
        admin = db.query(User).filter(User.email == "admin@namaskah.app").first()
        password_valid = verify_password("Namaskah@Admin2024", admin.password_hash)
        
        print("\n🎯 ADMIN LOGIN CREDENTIALS:")
        print("   📧 Email: admin@namaskah.app")
        print("   🔑 Password: Namaskah@Admin2024")
        print(f"   ✅ Password Valid: {password_valid}")
        print(f"   👑 Is Admin: {admin.is_admin}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Fixing production admin login...")
    success = fix_admin_login()
    
    if success:
        print("\n✅ Admin login fixed! Try logging in now.")
    else:
        print("\n❌ Failed to fix admin login. Check the error above.")