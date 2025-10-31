#!/usr/bin/env python3
"""Setup script for Render deployment"""
from app.core.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password

def create_admin_for_render():
    """Create admin user for Render deployment"""
    print("🚀 Setting up admin user for production...")
    
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if admin:
            print("👤 Admin user already exists - updating credentials...")
            # Update to ensure correct password and permissions
            admin.password_hash = hash_password("Namaskah@Admin2024")
            admin.is_admin = True
            admin.email_verified = True
            admin.credits = max(admin.credits, 1000.0)  # Ensure minimum credits
            db.commit()
            print("✅ Admin user updated successfully")
            return
        
        # Create admin user
        from app.utils.security import generate_secure_id
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
        
        print("✅ Admin user created successfully!")
        print("   📧 Email: admin@namaskah.app")
        print("   🔑 Password: Namaskah@Admin2024")
        print(f"   🆔 ID: {admin_user.id}")
        print(f"   💰 Credits: ${admin_user.credits}")
        
        # Verify the user was created correctly
        from app.utils.security import verify_password
        password_valid = verify_password("Namaskah@Admin2024", admin_user.password_hash)
        print(f"   🔐 Password verification: {'✅ Valid' if password_valid else '❌ Invalid'}")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_for_render()