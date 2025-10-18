#!/usr/bin/env python3
"""Fix admin account - create new working admin credentials"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import bcrypt
from datetime import datetime, timezone

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sms.db")

# Fix for PostgreSQL URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

try:
    # New admin credentials
    NEW_EMAIL = "admin@namaskah.app"
    NEW_PASSWORD = "Namaskah@Admin2024"
    
    print(f"\n🔧 Creating/Updating admin account...")
    print(f"Email: {NEW_EMAIL}")
    print(f"Password: {NEW_PASSWORD}")
    
    # Hash the password
    password_hash = bcrypt.hashpw(NEW_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Check if admin exists
    result = db.execute(text("SELECT id, email FROM users WHERE email = :email"), {"email": NEW_EMAIL}).fetchone()
    
    if result:
        # Update existing admin
        print(f"\n✅ Admin user found: {result[0]}")
        db.execute(text("""
            UPDATE users 
            SET password_hash = :password_hash, 
                is_admin = true,
                email_verified = true
            WHERE email = :email
        """), {"password_hash": password_hash, "email": NEW_EMAIL})
        print("✅ Admin password updated")
    else:
        # Create new admin
        import secrets
        user_id = f"user_{datetime.now(timezone.utc).timestamp()}"
        referral_code = secrets.token_urlsafe(6)
        
        db.execute(text("""
            INSERT INTO users (id, email, password_hash, credits, free_verifications, is_admin, email_verified, referral_code, referral_earnings, created_at)
            VALUES (:id, :email, :password_hash, 100.0, 0.0, true, true, :referral_code, 0.0, :created_at)
        """), {
            "id": user_id,
            "email": NEW_EMAIL,
            "password_hash": password_hash,
            "referral_code": referral_code,
            "created_at": datetime.now(timezone.utc)
        })
        print(f"✅ Admin user created: {user_id}")
    
    db.commit()
    
    print("\n" + "="*60)
    print("✅ ADMIN ACCOUNT READY")
    print("="*60)
    print(f"Email: {NEW_EMAIL}")
    print(f"Password: {NEW_PASSWORD}")
    print("="*60)
    print("\nLogin at:")
    print("- https://namaskah.onrender.com/admin")
    print("- https://namaskah.onrender.com/app")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    db.rollback()
    sys.exit(1)
finally:
    db.close()
