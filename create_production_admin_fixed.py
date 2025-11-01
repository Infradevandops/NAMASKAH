#!/usr/bin/env python3
"""
Create production admin user for Namaskah SMS
"""
import asyncio
import sys
import os
from datetime import datetime, timezone

# Add the app directory to Python path
sys.path.append('.')

async def create_admin():
    """Create admin user in production database"""
    try:
        # Import after path setup
        from app.core.database import get_db
        from app.models.user import User
        from app.utils.security import hash_password
        from sqlalchemy.orm import Session
        
        print("🔧 Creating Production Admin User...")
        
        # Get database session
        db_gen = get_db()
        db: Session = next(db_gen)
        
        # Admin user details
        admin_email = "admin@namaskah.app"
        admin_password = "Admin123!Secure"  # Change this in production
        
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if existing_admin:
            print(f"⚠️  Admin user already exists: {admin_email}")
            
            # Update to admin role
            existing_admin.role = "admin"
            existing_admin.is_active = True
            existing_admin.credits = 100.0  # Give some credits
            db.commit()
            
            print("✅ Updated existing user to admin role")
            return True
        
        # Create new admin user
        hashed_password = hash_password(admin_password)
        
        admin_user = User(
            email=admin_email,
            password_hash=hashed_password,
            role="admin",
            is_active=True,
            credits=100.0,
            free_verifications=10.0,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print(f"📧 Email: {admin_email}")
        print(f"🔑 Password: {admin_password}")
        print(f"👤 User ID: {admin_user.id}")
        print(f"💰 Credits: {admin_user.credits}")
        
        # Close database connection
        db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """Test database connectivity"""
    try:
        from app.core.database import engine
        
        print("🔍 Testing database connection...")
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1").scalar()
            if result == 1:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database connection failed")
                return False
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

async def main():
    """Main function"""
    print("🚀 Namaskah SMS - Admin User Creation")
    print("=" * 40)
    
    # Test database connection first
    if not test_database_connection():
        print("❌ Cannot proceed without database connection")
        return
    
    print()
    
    # Create admin user
    success = await create_admin()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Admin user setup completed!")
        print("📝 Next steps:")
        print("   1. Test admin login on production")
        print("   2. Change default password")
        print("   3. Test admin panel access")
    else:
        print("❌ Admin user creation failed")

if __name__ == "__main__":
    asyncio.run(main())