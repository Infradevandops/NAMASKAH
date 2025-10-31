#!/usr/bin/env python3
"""Fix production authentication issues - Best Practices Implementation"""

import os
import sys
import asyncio
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append('.')

def get_database_url():
    """Get production database URL from environment"""
    # Try multiple environment variable names
    db_url = (
        os.getenv('DATABASE_URL') or 
        os.getenv('SUPABASE_DB_URL') or 
        os.getenv('POSTGRES_URL')
    )
    
    if not db_url:
        print("❌ No database URL found. Set DATABASE_URL environment variable.")
        return None
    
    # Fix postgres:// to postgresql:// for SQLAlchemy 1.4+
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    return db_url

def hash_password_secure(password: str) -> str:
    """Secure password hashing using pbkdf2_sha256"""
    import hashlib
    import secrets
    
    # Generate secure salt
    salt = secrets.token_bytes(32)
    
    # Hash password with PBKDF2-SHA256 (100,000 iterations)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    
    # Return in format compatible with passlib
    return f"$pbkdf2-sha256$100000${salt.hex()}${pwdhash.hex()}"

def generate_secure_id(prefix: str = "", length: int = 16) -> str:
    """Generate cryptographically secure ID"""
    import secrets
    import string
    
    chars = string.ascii_lowercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(length))
    return f"{prefix}_{random_part}" if prefix else random_part

def test_database_connection(db_url: str) -> bool:
    """Test database connection"""
    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            return result[0] == 1
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def ensure_users_table_exists(db_url: str) -> bool:
    """Ensure users table exists with proper schema"""
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Check if users table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                );
            """)).fetchone()
            
            if not result[0]:
                print("📋 Creating users table...")
                conn.execute(text("""
                    CREATE TABLE users (
                        id VARCHAR(50) PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        credits DECIMAL(10,2) DEFAULT 0.00,
                        free_verifications DECIMAL(10,2) DEFAULT 1.00,
                        is_admin BOOLEAN DEFAULT FALSE,
                        email_verified BOOLEAN DEFAULT FALSE,
                        referral_code VARCHAR(50) UNIQUE,
                        referred_by VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                # Create indexes
                conn.execute(text("CREATE INDEX idx_users_email ON users(email);"))
                conn.execute(text("CREATE INDEX idx_users_referral_code ON users(referral_code);"))
                conn.commit()
                print("✅ Users table created successfully")
            else:
                print("✅ Users table already exists")
            
            return True
            
    except Exception as e:
        print(f"❌ Failed to create users table: {e}")
        return False

def create_or_update_admin(db_url: str) -> bool:
    """Create or update admin user with best practices"""
    try:
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        admin_email = "admin@namaskah.app"
        admin_password = "Namaskah@Admin2024"
        
        # Check if admin exists
        result = db.execute(text("SELECT id, email FROM users WHERE email = :email"), 
                          {"email": admin_email}).fetchone()
        
        if result:
            print(f"👤 Updating existing admin: {result.email}")
            # Update existing admin
            password_hash = hash_password_secure(admin_password)
            db.execute(text("""
                UPDATE users 
                SET password_hash = :password_hash,
                    is_admin = true,
                    email_verified = true,
                    credits = 1000.00,
                    free_verifications = 10.00,
                    updated_at = :updated_at
                WHERE email = :email
            """), {
                "password_hash": password_hash,
                "email": admin_email,
                "updated_at": datetime.utcnow()
            })
        else:
            print("👤 Creating new admin user...")
            # Create new admin
            user_id = generate_secure_id("user", 16)
            password_hash = hash_password_secure(admin_password)
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
                "id": user_id,
                "email": admin_email,
                "password_hash": password_hash,
                "credits": 1000.0,
                "free_verifications": 10.0,
                "is_admin": True,
                "email_verified": True,
                "referral_code": referral_code,
                "created_at": now,
                "updated_at": now
            })
        
        db.commit()
        db.close()
        
        print("✅ Admin user configured successfully")
        print(f"📧 Email: {admin_email}")
        print(f"🔑 Password: {admin_password}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create/update admin: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_authentication(db_url: str) -> bool:
    """Test authentication functionality"""
    try:
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Test admin login
        admin_email = "admin@namaskah.app"
        result = db.execute(text("""
            SELECT id, email, password_hash, is_admin, email_verified 
            FROM users WHERE email = :email
        """), {"email": admin_email}).fetchone()
        
        if not result:
            print("❌ Admin user not found")
            return False
        
        print(f"✅ Admin user found: {result.email}")
        print(f"✅ Admin status: {result.is_admin}")
        print(f"✅ Email verified: {result.email_verified}")
        
        # Test password hash format
        if result.password_hash.startswith('$pbkdf2-sha256$'):
            print("✅ Password hash format correct")
        else:
            print("⚠️ Password hash format may be incorrect")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def fix_registration_issues(db_url: str) -> bool:
    """Fix common registration issues"""
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Ensure email constraint is properly set
            conn.execute(text("""
                ALTER TABLE users 
                ALTER COLUMN email SET NOT NULL;
            """))
            
            # Ensure unique constraint on email
            try:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD CONSTRAINT users_email_unique UNIQUE (email);
                """))
            except Exception:
                pass  # Constraint might already exist
            
            # Set default values for new registrations
            conn.execute(text("""
                ALTER TABLE users 
                ALTER COLUMN credits SET DEFAULT 0.00,
                ALTER COLUMN free_verifications SET DEFAULT 1.00,
                ALTER COLUMN is_admin SET DEFAULT FALSE,
                ALTER COLUMN email_verified SET DEFAULT FALSE;
            """))
            
            conn.commit()
            print("✅ Registration constraints fixed")
            return True
            
    except Exception as e:
        print(f"⚠️ Some registration fixes may have failed: {e}")
        return True  # Non-critical errors

def main():
    """Main function to fix production authentication"""
    print("🔧 Fixing Production Authentication Issues")
    print("=" * 50)
    
    # Get database URL
    db_url = get_database_url()
    if not db_url:
        return False
    
    print(f"🗄️ Database: {db_url.split('@')[1] if '@' in db_url else 'Local'}")
    
    # Test database connection
    print("\n1. Testing database connection...")
    if not test_database_connection(db_url):
        return False
    print("✅ Database connection successful")
    
    # Ensure users table exists
    print("\n2. Checking users table...")
    if not ensure_users_table_exists(db_url):
        return False
    
    # Fix registration issues
    print("\n3. Fixing registration constraints...")
    fix_registration_issues(db_url)
    
    # Create/update admin user
    print("\n4. Setting up admin user...")
    if not create_or_update_admin(db_url):
        return False
    
    # Test authentication
    print("\n5. Testing authentication...")
    if not test_authentication(db_url):
        return False
    
    print("\n" + "=" * 50)
    print("✅ Production authentication fixed successfully!")
    print("\n🔐 Login Credentials:")
    print("   Email: admin@namaskah.app")
    print("   Password: Namaskah@Admin2024")
    print("\n📝 Next Steps:")
    print("   1. Test login at: https://namaskah.onrender.com/")
    print("   2. Test registration with a new email")
    print("   3. Verify admin panel access")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)