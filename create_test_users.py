#!/usr/bin/env python3
from passlib.hash import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import secrets

engine = create_engine("sqlite:///./sms.db")
Session = sessionmaker(bind=engine)
db = Session()

users = [
    ("admin@namaskah.app", "admin123", 100.0, True),
    ("user@namaskah.app", "user123", 5.0, False),
    ("test@example.com", "test123", 5.0, False),
]

for email, password, credits, is_admin in users:
    password_hash = bcrypt.hash(password)
    db.execute(f"""
        INSERT OR REPLACE INTO users (id, email, password_hash, credits, is_admin, referral_code, created_at)
        VALUES ('{email.split('@')[0]}_{int(datetime.now(timezone.utc).timestamp())}', 
                '{email}', 
                '{password_hash}', 
                {credits}, 
                {1 if is_admin else 0},
                '{secrets.token_urlsafe(6)}',
                '{datetime.now(timezone.utc).isoformat()}')
    """)
    print(f"✅ Created: {email} / {password}")

db.commit()
print("\n✅ All users created!")
