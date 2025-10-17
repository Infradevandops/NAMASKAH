"""Create admin user with credentials: admin@namaskah.app / Admin@2024!"""
import sqlite3
from passlib.hash import bcrypt

# Connect to database
conn = sqlite3.connect('namaskah.db')
cursor = conn.cursor()

# Check if admin exists
cursor.execute("SELECT id FROM users WHERE email = 'admin@namaskah.app'")
admin = cursor.fetchone()

# Hash password using passlib (same as backend)
password_hash = bcrypt.hash('Admin@2024!')

if admin:
    # Update existing admin
    cursor.execute("""
        UPDATE users 
        SET password_hash = ?, is_admin = 1, credits = 100.0 
        WHERE email = 'admin@namaskah.app'
    """, (password_hash,))
    print("✅ Admin password updated!")
else:
    # Create new admin
    import time
    import secrets
    user_id = f"user_{time.time()}"
    referral_code = secrets.token_urlsafe(6)
    
    cursor.execute("""
        INSERT INTO users (id, email, password_hash, credits, free_verifications, is_admin, email_verified, referral_code, created_at)
        VALUES (?, ?, ?, 100.0, 0.0, 1, 1, ?, datetime('now'))
    """, (user_id, 'admin@namaskah.app', password_hash, referral_code))
    print("✅ Admin created!")

conn.commit()
conn.close()

print("\n📧 Email: admin@namaskah.app")
print("🔑 Password: Admin@2024!")
print("🌐 Access: /admin")
