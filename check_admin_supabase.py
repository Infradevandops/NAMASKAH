#!/usr/bin/env python3
"""Check admin user in Supabase"""

import os
os.environ['ENVIRONMENT'] = 'development'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User

DATABASE_URL = "postgresql://postgres:ryskyx-8Padsa-timtabodh@db.oegyaxxlzmogrtgmhrcy.supabase.co:5432/postgres"

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    admin = db.query(User).filter(User.email == "admin@namaskah.app").first()
    
    if admin:
        print(f"✅ Admin exists:")
        print(f"   Email: {admin.email}")
        print(f"   Admin: {admin.is_admin}")
        print(f"   Active: {admin.is_active}")
        print(f"   Credits: {admin.credits}")
        print(f"   ID: {admin.id}")
    else:
        print("❌ Admin user not found")
    
    db.close()
    
except Exception as e:
    print(f"❌ Error: {e}")