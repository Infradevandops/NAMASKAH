"""Reset database with new schema"""
import os

# Remove existing database if it exists
if os.path.exists("sms.db"):
    os.remove("sms.db")
    print("🗑️ Removed existing database")

from main import Base, engine, User, Verification, Transaction, SessionLocal
from passlib.hash import bcrypt
from datetime import datetime, timezone

# Create all tables
Base.metadata.create_all(bind=engine)
print("✅ Database created with new schema")

# Create users
db = SessionLocal()

users = [
    {"email": "admin@namaskah.app", "password": "admin123", "credits": 100.0, "is_admin": True},
    {"email": "user@namaskah.app", "password": "user123", "credits": 5.0, "is_admin": False},
    {"email": "test@example.com", "password": "test123", "credits": 5.0, "is_admin": False}
]

for u in users:
    user = User(
        id=f"user_{datetime.now(timezone.utc).timestamp()}_{u['email']}",
        email=u["email"],
        password_hash=bcrypt.hash(u["password"]),
        credits=u["credits"],
        is_admin=u["is_admin"]
    )
    db.add(user)
    print(f"✅ Created: {u['email']} | Credits: ${u['credits']} | Admin: {u['is_admin']}")

db.commit()
db.close()

print("\n🎉 Database ready!")
print("\n📝 Login:")
print("Admin: admin@namaskah.app / admin123")
print("User:  user@namaskah.app / user123")
