"""Setup API for production initialization."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.utils.security import hash_password

router = APIRouter(prefix="/setup", tags=["Setup"])

@router.post("/create-admin")
def create_admin(db: Session = Depends(get_db)):
    """Create admin user for production."""
    try:
        # Check if admin exists
        existing = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if existing:
            return {"message": "Admin already exists"}
        
        # Create admin
        admin = User(
            email="admin@namaskah.app",
            password_hash=hash_password("Namaskah@Admin2024"),
            credits=1000.0,
            free_verifications=10,
            is_admin=True,
            is_verified=True
        )
        
        db.add(admin)
        db.commit()
        
        return {"message": "Admin created successfully"}
        
    except Exception as e:
        return {"error": str(e)}