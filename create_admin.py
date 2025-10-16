"""Create admin user"""
import os
from datetime import datetime, timezone
import secrets
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from passlib.hash import bcrypt
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sms.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    credits = Column(Float, default=0.0)
    free_verifications = Column(Float, default=1.0)
    is_admin = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String)
    reset_token = Column(String)
    reset_token_expires = Column(DateTime)
    referral_code = Column(String, unique=True)
    referred_by = Column(String)
    referral_earnings = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

db = SessionLocal()

# Check if admin exists
admin = db.query(User).filter(User.email == "admin@namaskah.app").first()

if not admin:
    admin = User(
        id=f"admin_{datetime.now(timezone.utc).timestamp()}",
        email="admin@namaskah.app",
        password_hash=bcrypt.hash("Admin@2024!"),
        credits=1000.0,
        free_verifications=0.0,
        is_admin=True,
        referral_code=secrets.token_urlsafe(6),
        email_verified=True
    )
    db.add(admin)
    db.commit()
    print("✅ Admin user created successfully!")
else:
    # Update password
    admin.password_hash = bcrypt.hash("Admin@2024!")
    admin.is_admin = True
    db.commit()
    print("✅ Admin user updated!")

print(f"\n📧 Email: admin@namaskah.app")
print(f"🔑 Password: Admin@2024!")
print(f"\n🔗 Login at: http://localhost:8000/app")
print(f"🔗 Admin Panel: http://localhost:8000/admin")

db.close()
