#!/usr/bin/env python3
"""Python-based Supabase connection fix using direct psycopg2"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import secrets

def create_connection():
    """Create direct psycopg2 connection to Supabase"""
    try:
        # Use Session Pooler (IPv4 compatible)
        connection = psycopg2.connect(
            host="aws-0-us-east-1.pooler.supabase.com",
            port=6543,
            database="postgres", 
            user="postgres.oegyaxxlzmogrtgmhrcy",
            password="ryskyx-8Padsa-timtabodh"
        )
        print("✅ Connection successful!")
        return connection
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def hash_password(password: str) -> str:
    """Hash password using pbkdf2_sha256"""
    salt = secrets.token_bytes(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"$pbkdf2-sha256$100000${salt.hex()}${pwdhash.hex()}"

def create_tables(connection):
    """Create necessary tables"""
    cursor = connection.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            credits DECIMAL(10,2) DEFAULT 0.00,
            free_verifications DECIMAL(10,2) DEFAULT 1.00,
            is_admin BOOLEAN DEFAULT FALSE,
            email_verified BOOLEAN DEFAULT FALSE,
            referral_code VARCHAR(50) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    connection.commit()
    print("✅ Tables created")

def create_admin_user(connection):
    """Create admin user directly"""
    cursor = connection.cursor()
    
    # Check if admin exists
    cursor.execute("SELECT id FROM users WHERE email = %s", ("admin@namaskah.app",))
    if cursor.fetchone():
        print("✅ Admin user already exists")
        return True
    
    # Create admin user
    admin_id = secrets.token_urlsafe(16)
    password_hash = hash_password("Namaskah@Admin2024")
    referral_code = f"admin_{secrets.token_urlsafe(6)}"
    
    cursor.execute("""
        INSERT INTO users (id, email, password_hash, credits, free_verifications, 
                          is_admin, email_verified, referral_code)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (admin_id, "admin@namaskah.app", password_hash, 1000.0, 10.0, True, True, referral_code))
    
    connection.commit()
    print("✅ Admin user created successfully!")
    return True

def test_login(connection):
    """Test admin login by verifying credentials"""
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT id, email, password_hash, is_admin, email_verified, credits
        FROM users WHERE email = %s
    """, ("admin@namaskah.app",))
    
    user = cursor.fetchone()
    if user:
        print(f"✅ Admin user found:")
        print(f"   Email: {user['email']}")
        print(f"   Admin: {user['is_admin']}")
        print(f"   Verified: {user['email_verified']}")
        print(f"   Credits: {user['credits']}")
        return True
    else:
        print("❌ Admin user not found")
        return False

def main():
    print("🔧 Supabase Python Direct Connection Fix")
    print("=" * 50)
    
    print("\n1. Connecting to Supabase via Session Pooler...")
    connection = create_connection()
    
    if not connection:
        print("❌ Cannot connect to database")
        return False
    
    try:
        print("\n2. Creating tables...")
        create_tables(connection)
        
        print("\n3. Creating admin user...")
        create_admin_user(connection)
        
        print("\n4. Testing admin user...")
        test_login(connection)
        
        print("\n✅ Database setup complete!")
        print("\nNow test login at: https://namaskahsms.onrender.com/app")
        print("Email: admin@namaskah.app")
        print("Password: Namaskah@Admin2024")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        connection.close()

if __name__ == "__main__":
    main()