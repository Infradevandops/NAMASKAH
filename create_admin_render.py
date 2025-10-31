#!/usr/bin/env python3
"""Create admin user for Render production"""

import os
import sys
sys.path.append('.')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import hashlib
import secrets
import string
from datetime import datetime

def hash_password(password: str) -> str:
    """Hash password using pbkdf2_sha256"""
    salt = secrets.token_bytes(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"$pbkdf2-sha256$100000${salt.hex()}${pwdhash.hex()}"

def generate_secure_id(prefix: str = "", length: int = 16) -> str:
    """Generate secure random ID"""
    chars = string.ascii_lowercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(length))
    return f"{prefix}_{random_part}" if prefix else random_part

def main():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return
    
    try:
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Check if admin exists
        result = db.execute(text("SELECT id FROM users WHERE email = 'admin@namaskah.app'")).fetchone()
        
        if result:
            # Update existing admin
            password_hash = hash_password("Namaskah@Admin2024")
            db.execute(text("""
                UPDATE users 
                SET password_hash = :password_hash, 
                    is_admin = true, 
                    email_verified = true,
                    updated_at = :updated_at
                WHERE email = 'admin@namaskah.app'
            """), {
                'password_hash': password_hash,
                'updated_at': datetime.utcnow()
            })
            print("✅ Updated existing admin")
        else:
            # Create new admin
            user_id = generate_secure_id("user", 16)
            password_hash = hash_password("Namaskah@Admin2024")
            referral_code = generate_secure_id("admin", 6)
            now = datetime.utcnow()
            
            db.execute(text("""
                INSERT INTO users (
                    id, email, password_hash, credits, free_verifications,
                    is_admin, email_verified, referral_code, created_at, updated_at
                ) VALUES (
                    :id, :email, :password_hash, :credits, :free_verifications,
                    :is_admin, :email_verified, :referral_code, :created_at, :updated_at
                )
            """), {
                'id': user_id,
                'email': 'admin@namaskah.app',
                'password_hash': password_hash,
                'credits': 1000.0,
                'free_verifications': 10.0,
                'is_admin': True,
                'email_verified': True,
                'referral_code': referral_code,
                'created_at': now,
                'updated_at': now
            })
            print("✅ Created new admin")
        
        db.commit()
        db.close()
        print("🎯 Admin credentials: admin@namaskah.app / Namaskah@Admin2024")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()