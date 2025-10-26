"""Authentication service for user management and JWT operations."""
from typing import Optional, Dict, Any
from datetime import timedelta
from sqlalchemy.orm import Session
from app.models.user import User, APIKey
from app.services.base import BaseService
from app.utils.security import (
    hash_password, verify_password, create_access_token, 
    verify_token, generate_api_key, generate_secure_id
)
from app.core.exceptions import ValidationError


class AuthService(BaseService[User]):
    """Authentication service for user operations."""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def register_user(self, email: str, password: str, referral_code: Optional[str] = None) -> User:
        """Register a new user account."""
        # Check if user exists
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            raise ValidationError("Email already registered")
        
        # Create user
        user_data = {
            "email": email,
            "password_hash": hash_password(password),
            "referral_code": generate_secure_id("ref", 6)
        }
        
        # Handle referral
        if referral_code:
            referrer = self.db.query(User).filter(User.referral_code == referral_code).first()
            if referrer:
                user_data["referred_by"] = referrer.id
                user_data["free_verifications"] = 2.0  # Bonus for being referred
        
        return self.create(**user_data)
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            return None
        return user
    
    @staticmethod
    def create_user_token(user: User, expires_hours: int = 24 * 30) -> str:
        """Create JWT token for user."""
        data = {"user_id": user.id, "email": user.email}
        expires_delta = timedelta(hours=expires_hours)
        return create_access_token(data, expires_delta)
    
    @staticmethod
    def verify_user_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload."""
        return verify_token(token)
    
    def get_user_from_token(self, token: str) -> Optional[User]:
        """Get user from JWT token."""
        payload = self.verify_user_token(token)
        if not payload:
            return None
        
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        return self.get_by_id(user_id)
    
    def create_api_key(self, user_id: str, name: str) -> APIKey:
        """Create API key for user."""
        api_key = APIKey(
            user_id=user_id,
            key=f"nsk_{generate_api_key()}",
            name=name
        )
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        return api_key
    
    def verify_api_key(self, key: str) -> Optional[User]:
        """Verify API key and return associated user."""
        api_key = self.db.query(APIKey).filter(
            APIKey.key == key,
            APIKey.is_active == True
        ).first()
        
        if not api_key:
            return None
        
        return self.get_by_id(api_key.user_id)
    
    def deactivate_api_key(self, key_id: str, user_id: str) -> bool:
        """Deactivate API key for user."""
        api_key = self.db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        ).first()
        
        if not api_key:
            return False
        
        self.db.delete(api_key)
        self.db.commit()
        return True
    
    def get_user_api_keys(self, user_id: str) -> list[APIKey]:
        """Get all API keys for user."""
        return self.db.query(APIKey).filter(APIKey.user_id == user_id).all()
    
    def update_password(self, user_id: str, new_password: str) -> bool:
        """Update user password."""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        user.password_hash = hash_password(new_password)
        user.update_timestamp()
        self.db.commit()
        return True
    
    def verify_admin_access(self, user_id: str) -> bool:
        """Verify user has admin access."""
        user = self.get_by_id(user_id)
        return user is not None and user.is_admin


def get_auth_service(db: Session) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db)