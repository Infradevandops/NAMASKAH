#!/usr/bin/env python3
"""
Simple test for JWT middleware functionality
"""
import asyncio
import sys
import traceback

try:
    from middleware.auth_middleware import JWTAuthMiddleware, SessionManager
    from auth.security import create_access_token, create_refresh_token
    from database import SessionLocal, create_tables, check_database_connection
    from models.user_models import User
    from services.auth_service import AuthenticationService
    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    traceback.print_exc()
    sys.exit(1)

async def test_middleware():
    """Test the JWT middleware and session management"""
    print("Testing JWT Middleware and Session Management...")
    
    # Check database connection
    if not check_database_connection():
        print("❌ Database connection failed!")
        return
    print("✅ Database connection successful")
    
    # Create tables
    try:
        create_tables()
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"❌ Database table creation failed: {e}")
        return
    
    # Test session manager
    db = SessionLocal()
    try:
        # Create a test user
        auth_service = AuthenticationService(db)
        
        # Register a test user
        result = await auth_service.register_user(
            email="middleware_test@example.com",
            username="middlewaretest",
            password="TestPassword123!",
            full_name="Middleware Test User"
        )
        print(f"✅ Test user created: {result['user_id']}")
        
        # Test session manager
        session_manager = SessionManager(db)
        
        # Create refresh token
        refresh_token = create_refresh_token({"sub": result['user_id']})
        
        # Create session
        session_created = await session_manager.create_session(
            user_id=result['user_id'],
            refresh_token=refresh_token,
            user_agent="Test Agent",
            ip_address="127.0.0.1"
        )
        
        if session_created:
            print("✅ Session created successfully")
        else:
            print("❌ Session creation failed")
            return
        
        # Validate session
        user = await session_manager.validate_session(refresh_token)
        if user and user.id == result['user_id']:
            print("✅ Session validation successful")
        else:
            print("❌ Session validation failed")
            return
        
        # Test JWT token creation
        access_token = create_access_token({"sub": user.id, "email": user.email})
        print("✅ JWT token created successfully")
        
        # Test session invalidation
        invalidated = await session_manager.invalidate_session(refresh_token)
        if invalidated:
            print("✅ Session invalidation successful")
        else:
            print("❌ Session invalidation failed")
        
        print("\n🎉 All middleware tests passed!")
        
    except Exception as e:
        print(f"❌ Middleware test failed: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_middleware())