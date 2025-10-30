#!/usr/bin/env python3
"""Export user data for migration"""
import json
from app.core.database import SessionLocal
from app.models.user import User

def export_users():
    """Export all user data to JSON"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        user_data = []
        
        for user in users:
            user_data.append({
                'email': user.email,
                'password_hash': user.password_hash,
                'credits': user.credits,
                'free_verifications': user.free_verifications,
                'is_admin': user.is_admin,
                'email_verified': user.email_verified,
                'referral_code': user.referral_code,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        
        with open('users_backup.json', 'w') as f:
            json.dump(user_data, f, indent=2)
            
        print(f"✅ Exported {len(user_data)} users to users_backup.json")
        
    finally:
        db.close()

if __name__ == "__main__":
    export_users()