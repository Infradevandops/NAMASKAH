#!/usr/bin/env python3
"""Setup script for Render deployment"""
import os
import sys
from app.core.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password

def create_admin_for_render():
    """Create admin user for Render deployment"""
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if admin:
            print("✅ Admin user already exists")
            return
        
        # Create admin user
        admin_user = User(
            email="admin@namaskah.app",
            password_hash=hash_password("Namaskah@Admin2024"),
            credits=1000.0,
            free_verifications=10,
            is_admin=True,
            is_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        print("✅ Admin user created for Render")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_for_render()