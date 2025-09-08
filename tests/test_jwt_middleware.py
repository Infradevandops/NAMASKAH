#!/usr/bin/env python3
"""
Unit tests for JWT Middleware and Session Management
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.user_models import Base, User, Session as UserSession, APIKey
from middleware.auth_middleware import JWTAuthMiddleware, SessionManager, get_current_user_from_middleware
from auth.security import create_access_token, create_refresh_token, generate_api_key, hash_api_key
from database import get_db

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_middleware.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

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

@pytest.fixture
def test_app():
    """Create a test FastAPI app with middleware"""
    app = FastAPI()
    
    # Add JWT middleware
    app.add_middleware(JWTAuthMiddleware, exclude_paths=["/public", "/health"])
    
    # Override database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Test routes
    @app.get("/public")
    async def public_endpoint():
        return {"message": "public"}
    
    @app.get("/protected")
    async def protected_endpoint(request: Request):
        user = get_current_user_from_middleware(request)
        return {"message": "protected", "user_id": user.id}
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app

@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    from auth.security import hash_password
    
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("TestPassword123!"),
        full_name="Test User",
        is_active=True,
        is_verified=True
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user

class TestJWTMiddleware:
    """Test cases for JWT Middleware"""
    
    def test_public_endpoint_no_auth_required(self, test_app):
        """Test that public endpoints don't require authentication"""
        client = TestClient(test_app)
        response = client.get("/public")
        
        assert response.status_code == 200
        assert response.json() == {"message": "public"}
    
    def test_health_endpoint_no_auth_required(self, test_app):
        """Test that health endpoint doesn't require authentication"""
        client = TestClient(test_app)
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_protected_endpoint_no_token(self, test_app):
        """Test protected endpoint without token returns 401"""
        client = TestClient(test_app)
        response = client.get("/protected")
        
        assert response.status_code == 401
        assert "Missing authorization header" in response.json()["detail"]
    
    def test_protected_endpoint_invalid_token_format(self, test_app):
        """Test protected endpoint with invalid token format"""
        client = TestClient(test_app)
        response = client.get(
            "/protected",
            headers={"Authorization": "InvalidFormat token123"}
        )
        
        assert response.status_code == 401
        assert "Invalid authorization header format" in response.json()["detail"]
    
    def test_protected_endpoint_invalid_token(self, test_app):
        """Test protected endpoint with invalid token"""
        client = TestClient(test_app)
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]
    
    def test_protected_endpoint_valid_jwt_token(self, test_app, test_user):
        """Test protected endpoint with valid JWT token"""
        # Create valid JWT token
        token = create_access_token({"sub": test_user.id, "email": test_user.email})
        
        client = TestClient(test_app)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "protected"
        assert response.json()["user_id"] == test_user.id
    
    def test_protected_endpoint_valid_api_key(self, test_app, test_user, db_session):
        """Test protected endpoint with valid API key"""
        # Create API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        
        db_api_key = APIKey(
            user_id=test_user.id,
            key_hash=key_hash,
            name="Test Key",
            is_active=True
        )
        
        db_session.add(db_api_key)
        db_session.commit()
        
        client = TestClient(test_app)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "protected"
        assert response.json()["user_id"] == test_user.id
    
    def test_protected_endpoint_expired_jwt_token(self, test_app, test_user):
        """Test protected endpoint with expired JWT token"""
        # Create expired token
        token = create_access_token(
            {"sub": test_user.id, "email": test_user.email},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        client = TestClient(test_app)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]
    
    def test_protected_endpoint_inactive_user(self, test_app, test_user, db_session):
        """Test protected endpoint with token for inactive user"""
        # Deactivate user
        test_user.is_active = False
        db_session.commit()
        
        # Create valid token
        token = create_access_token({"sub": test_user.id, "email": test_user.email})
        
        client = TestClient(test_app)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

class TestSessionManager:
    """Test cases for Session Manager"""
    
    @pytest.mark.asyncio
    async def test_create_session_success(self, db_session, test_user):
        """Test successful session creation"""
        session_manager = SessionManager(db_session)
        refresh_token = create_refresh_token({"sub": test_user.id})
        
        result = await session_manager.create_session(
            user_id=test_user.id,
            refresh_token=refresh_token,
            user_agent="Test Agent",
            ip_address="127.0.0.1"
        )
        
        assert result is True
        
        # Verify session was created
        session = db_session.query(UserSession).filter(
            UserSession.refresh_token == refresh_token
        ).first()
        
        assert session is not None
        assert session.user_id == test_user.id
        assert session.user_agent == "Test Agent"
        assert session.ip_address == "127.0.0.1"
        assert session.is_active is True
    
    @pytest.mark.asyncio
    async def test_validate_session_success(self, db_session, test_user):
        """Test successful session validation"""
        session_manager = SessionManager(db_session)
        refresh_token = create_refresh_token({"sub": test_user.id})
        
        # Create session
        await session_manager.create_session(
            user_id=test_user.id,
            refresh_token=refresh_token
        )
        
        # Validate session
        user = await session_manager.validate_session(refresh_token)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_validate_session_invalid_token(self, db_session):
        """Test session validation with invalid token"""
        session_manager = SessionManager(db_session)
        
        user = await session_manager.validate_session("invalid_token")
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_validate_session_expired(self, db_session, test_user):
        """Test session validation with expired session"""
        session_manager = SessionManager(db_session)
        refresh_token = create_refresh_token({"sub": test_user.id})
        
        # Create expired session
        session = UserSession(
            user_id=test_user.id,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired
            is_active=True
        )
        
        db_session.add(session)
        db_session.commit()
        
        # Try to validate expired session
        user = await session_manager.validate_session(refresh_token)
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_invalidate_session_success(self, db_session, test_user):
        """Test successful session invalidation"""
        session_manager = SessionManager(db_session)
        refresh_token = create_refresh_token({"sub": test_user.id})
        
        # Create session
        await session_manager.create_session(
            user_id=test_user.id,
            refresh_token=refresh_token
        )
        
        # Invalidate session
        result = await session_manager.invalidate_session(refresh_token)
        
        assert result is True
        
        # Verify session is inactive
        session = db_session.query(UserSession).filter(
            UserSession.refresh_token == refresh_token
        ).first()
        
        assert session.is_active is False
    
    @pytest.mark.asyncio
    async def test_invalidate_all_user_sessions(self, db_session, test_user):
        """Test invalidating all sessions for a user"""
        session_manager = SessionManager(db_session)
        
        # Create multiple sessions
        tokens = []
        for i in range(3):
            token = create_refresh_token({"sub": test_user.id})
            tokens.append(token)
            await session_manager.create_session(
                user_id=test_user.id,
                refresh_token=token
            )
        
        # Invalidate all sessions
        result = await session_manager.invalidate_all_user_sessions(test_user.id)
        
        assert result is True
        
        # Verify all sessions are inactive
        active_sessions = db_session.query(UserSession).filter(
            UserSession.user_id == test_user.id,
            UserSession.is_active == True
        ).count()
        
        assert active_sessions == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, db_session, test_user):
        """Test cleanup of expired sessions"""
        session_manager = SessionManager(db_session)
        
        # Create expired sessions
        for i in range(3):
            token = create_refresh_token({"sub": test_user.id})
            session = UserSession(
                user_id=test_user.id,
                refresh_token=token,
                expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired
                is_active=True
            )
            db_session.add(session)
        
        # Create active session
        active_token = create_refresh_token({"sub": test_user.id})
        active_session = UserSession(
            user_id=test_user.id,
            refresh_token=active_token,
            expires_at=datetime.utcnow() + timedelta(hours=1),  # Active
            is_active=True
        )
        db_session.add(active_session)
        db_session.commit()
        
        # Cleanup expired sessions
        count = await session_manager.cleanup_expired_sessions()
        
        assert count == 3
        
        # Verify only active session remains active
        active_sessions = db_session.query(UserSession).filter(
            UserSession.user_id == test_user.id,
            UserSession.is_active == True
        ).count()
        
        assert active_sessions == 1

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])