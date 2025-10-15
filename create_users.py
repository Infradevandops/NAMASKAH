"""Create default admin and test users"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.hash import bcrypt
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

# Import models
from main import User, Base

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sms.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Default users
users = [
    {
        "email": "admin@namaskah.app",
        "password": "admin123",
        "role": "Admin",
        "is_admin": True,
        "credits": 100.0
    },
    {
        "email": "user@namaskah.app", 
        "password": "user123",
        "role": "User",
        "is_admin": False,
        "credits": 5.0
    },
    {
        "email": "test@example.com",
        "password": "test123",
        "role": "User",
        "is_admin": False,
        "credits": 5.0
    }
]

print("🔧 Creating default users...\n")

for user_data in users:
    # Check if user exists
    existing = db.query(User).filter(User.email == user_data["email"]).first()
    
    if existing:
        print(f"⚠️  {user_data['email']} already exists - skipping")
        continue
    
    # Create user
    user = User(
        id=f"user_{datetime.now(timezone.utc).timestamp()}_{user_data['email']}",
        email=user_data["email"],
        password_hash=bcrypt.hash(user_data["password"]),
        credits=user_data.get("credits", 5.0),
        is_admin=user_data.get("is_admin", False)
    )
    
    db.add(user)
    db.commit()
    
    print(f"✅ Created {user_data['role']}: {user_data['email']}")
    print(f"   Password: {user_data['password']}\n")

db.close()

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("🎉 Default users created successfully!")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
print("📝 Login Credentials:\n")
print("👤 Admin Account:")
print("   Email:    admin@namaskah.app")
print("   Password: admin123\n")
print("👤 Test User:")
print("   Email:    user@namaskah.app")
print("   Password: user123\n")
print("👤 Demo User:")
print("   Email:    test@example.com")
print("   Password: test123\n")
print("🌐 Visit: http://localhost:8000")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
