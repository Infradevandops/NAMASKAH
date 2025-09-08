#!/usr/bin/env python3
"""
Test imports for middleware
"""
try:
    print("Testing imports...")
    
    from middleware.auth_middleware import JWTAuthMiddleware
    print("✅ JWTAuthMiddleware imported")
    
    from middleware.auth_middleware import SessionManager
    print("✅ SessionManager imported")
    
    from auth.security import create_access_token
    print("✅ create_access_token imported")
    
    print("🎉 All imports successful!")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()