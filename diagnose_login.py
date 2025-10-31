#!/usr/bin/env python3
"""Diagnose login issues"""

import os
import sys
sys.path.append('.')

def diagnose_login_issue():
    """Diagnose the login issue step by step"""
    
    print("🔍 DIAGNOSING LOGIN ISSUE...")
    print("=" * 50)
    
    # 1. Check environment
    print("1️⃣ ENVIRONMENT CHECK:")
    env = os.getenv('ENVIRONMENT', 'development')
    database_url = os.getenv('DATABASE_URL', 'not set')
    print(f"   Environment: {env}")
    print(f"   Database URL: {database_url[:50]}..." if len(database_url) > 50 else f"   Database URL: {database_url}")
    
    # 2. Check database connection
    print("\n2️⃣ DATABASE CONNECTION:")
    try:
        from app.core.database import SessionLocal
        from app.models.user import User
        
        db = SessionLocal()
        # Test query
        user_count = db.query(User).count()
        print(f"   ✅ Connection successful")
        print(f"   👥 Total users: {user_count}")
        
        # 3. Check admin user
        print("\n3️⃣ ADMIN USER CHECK:")
        admin = db.query(User).filter(User.email == "admin@namaskah.app").first()
        
        if admin:
            print(f"   ✅ Admin user found")
            print(f"   📧 Email: {admin.email}")
            print(f"   🆔 ID: {admin.id}")
            print(f"   👑 Is Admin: {admin.is_admin}")
            print(f"   ✉️ Email Verified: {admin.email_verified}")
            
            # 4. Test password
            print("\n4️⃣ PASSWORD TEST:")
            from app.utils.security import verify_password
            password_valid = verify_password("Namaskah@Admin2024", admin.password_hash)
            print(f"   🔑 Password 'Namaskah@Admin2024': {'✅ Valid' if password_valid else '❌ Invalid'}")
            
            if not password_valid:
                print("   🔧 FIXING PASSWORD...")
                from app.utils.security import hash_password
                admin.password_hash = hash_password("Namaskah@Admin2024")
                db.commit()
                print("   ✅ Password updated")
            
        else:
            print("   ❌ Admin user NOT found")
            print("   🔧 CREATING ADMIN USER...")
            
            from app.utils.security import hash_password, generate_secure_id
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
            print(f"   ✅ Admin user created with ID: {admin_user.id}")
        
        # 5. Test authentication service
        print("\n5️⃣ AUTHENTICATION SERVICE TEST:")
        from app.services.auth_service import get_auth_service
        auth_service = get_auth_service(db)
        
        authenticated_user = auth_service.authenticate_user("admin@namaskah.app", "Namaskah@Admin2024")
        if authenticated_user:
            print("   ✅ Authentication service working")
            print(f"   👤 Authenticated user: {authenticated_user.email}")
        else:
            print("   ❌ Authentication service failed")
        
        db.close()
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 50)
    print("🎯 FINAL CREDENTIALS:")
    print("   📧 Email: admin@namaskah.app")
    print("   🔑 Password: Namaskah@Admin2024")
    print("   🌐 Login URL: /auth/login")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    diagnose_login_issue()