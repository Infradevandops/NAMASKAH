#!/usr/bin/env python3
"""Create admin user with production credentials"""

import os
import sys
sys.path.append('.')

try:
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.utils.security import hash_password
    from app.utils.security import generate_secure_id
    
    # Create admin user
    db = SessionLocal()
    
    # Clear ALL existing users
    existing_users = db.query(User).all()
    for user in existing_users:
        print(f"🗑️ Deleting user: {user.email}")
        db.delete(user)
    db.commit()
    
    # Create new admin user
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
    db.close()
    
    print("✅ Admin user created successfully!")
    print(f"📧 Email: admin@namaskah.app")
    print(f"🔑 Password: Namaskah@Admin2024")
    print(f"💰 Credits: $1000.0")
    print(f"🆓 Free verifications: 10")
    print(f"👑 Admin: True")
    print(f"🆔 User ID: {admin_user.id}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)