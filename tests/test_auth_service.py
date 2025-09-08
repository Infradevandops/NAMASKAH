#!/usr/bin/env python3
"""
Unit tests for Authentication Service
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.user_models import Base, User, Session as UserSession
from services.auth_service import AuthenticationService
from auth.security import hash_password, verify_password, create_access_token, verify_token

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """Create a test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

class TestAuthenticationService:
    """Test cases for AuthenticationService"""
    
    @pytest.mark.asyncio
    async def test_user_registration_success(self, db_session):
        """Test successful user registration"""
        auth_service = AuthenticationService(db_session)
        
        result = await auth_service.register_user(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            full_name="Test User"
        )
        
        assert result["email"] == "test@example.com"
        assert result["username"] == "testuser"
        assert "user_id" in result
        assert "verification_token" in result
        
        # Verify user was created in database
        user = db_session.query(User).filter(User.email == "test@example.com").first()
        assert user is not None
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_verified is False
    
    @pytest.mark.asyncio
    async def test_user_registration_duplicate_email(self, db_session):
        """Test registration with duplicate email"""
        auth_service = AuthenticationService(db_session)
        
        # Register first user
        await auth_service.register_user(
            email="test@example.com",
            username="testuser1",
            password="TestPassword123!"
        )
        
        # Try to register with same email
        with pytest.raises(Exception):  # Should raise HTTPException
            await auth_service.register_user(
                email="test@example.com",
                username="testuser2",
                password="TestPassword123!"
            )
    
    @pytest.mark.asyncio
    async def test_user_registration_weak_password(self, db_session):
        """Test registration with weak password"""
        auth_service = AuthenticationService(db_session)
        
        with pytest.raises(Exception):  # Should raise HTTPException for weak password
            await auth_service.register_user(
                email="test@example.com",
                username="testuser",
                password="weak"
            )
    
    @pytest.mark.asyncio
    async def test_user_login_success(self, db_session):
        """Test successful user login"""
        auth_service = AuthenticationService(db_session)
        
        # Register user first
        await auth_service.register_user(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            full_name="Test User"
        )
        
        # Login
        result = await auth_service.authenticate_user(
            email="test@example.com",
            password="TestPassword123!"
        )
        
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        assert result["expires_in"] == 900  # 15 minutes
        assert result["user"]["email"] == "test@example.com"
        assert result["user"]["username"] == "testuser"
        
        # Verify session was created
        session = db_session.query(UserSession).filter(
            UserSession.refresh_token == result["refresh_token"]
        ).first()
        assert session is not None
        assert session.is_active is True
    
    @pytest.mark.asyncio
    async def test_user_login_invalid_credentials(self, db_session):
        """Test login with invalid credentials"""
        auth_service = AuthenticationService(db_session)
        
        # Register user first
        await auth_service.register_user(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!"
        )
        
        # Try login with wrong password
        with pytest.raises(Exception):  # Should raise HTTPException
            await auth_service.authenticate_user(
                email="test@example.com",
                password="WrongPassword123!"
            )
        
        # Try login with wrong email
        with pytest.raises(Exception):  # Should raise HTTPException
            await auth_service.authenticate_user(
                email="wrong@example.com",
                password="TestPassword123!"
            )
    
    @pytest.mark.asyncio
    async def test_token_refresh_success(self, db_session):
        """Test successful token refresh"""
        auth_service = AuthenticationService(db_session)
        
        # Register and login user
        await auth_service.register_user(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!"
        )
        
        login_result = await auth_service.authenticate_user(
            email="test@example.com",
            password="TestPassword123!"
        )
        
        # Refresh token
        refresh_result = await auth_service.refresh_token(
            login_result["refresh_token"]
        )
        
        assert "access_token" in refresh_result
        assert refresh_result["token_type"] == "bearer"
        assert refresh_result["expires_in"] == 900
        
        # Verify new access token is valid
        payload = verify_token(refresh_result["access_token"], "access")
        assert payload is not None
        assert payload["type"] == "access"
    
    @pytest.mark.asyncio
    async def test_token_refresh_invalid_token(self, db_session):
        """Test token refresh with invalid token"""
        auth_service = AuthenticationService(db_session)
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await auth_service.refresh_token("invalid_token")
    
    @pytest.mark.asyncio
    async def test_user_logout_success(self, db_session):
        """Test successful user logout"""
        auth_service = AuthenticationService(db_session)
        
        # Register and login user
        await auth_service.register_user(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!"
        )
        
        login_result = await auth_service.authenticate_user(
            email="test@example.com",
            password="TestPassword123!"
        )
        
        # Logout
        logout_result = await auth_service.logout(login_result["refresh_token"])
        
        assert logout_result["message"] == "Logged out successfully"
        
        # Verify session is deactivated
        session = db_session.query(UserSession).filter(
            UserSession.refresh_token == login_result["refresh_token"]
        ).first()
        assert session.is_active is False
    
    @pytest.mark.asyncio
    async def test_email_verification_success(self, db_session):
        """Test successful email verification"""
        auth_service = AuthenticationService(db_session)
        
        # Register user
        result = await auth_service.register_user(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!"
        )
        
        # Verify email
        verify_result = await auth_service.verify_email(result["verification_token"])
        
        assert verify_result["message"] == "Email verified successfully"
        
        # Check user is verified
        user = db_session.query(User).filter(User.email == "test@example.com").first()
        assert user.is_verified is True
        assert user.email_verification_token is None

class TestPasswordSecurity:
    """Test cases for password security functions"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert hashed != password  # Password should be hashed
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)
        
        assert token is not None
        
        # Verify token
        payload = verify_token(token, "access")
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
    
    def test_jwt_token_expiration(self):
        """Test JWT token expiration"""
        data = {"sub": "user123"}
        # Create token with very short expiration
        token = create_access_token(data, timedelta(seconds=-1))  # Already expired
        
        # Should fail verification due to expiration
        payload = verify_token(token, "access")
        assert payload is None

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])