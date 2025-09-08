#!/usr/bin/env python3
"""
Simple test app to verify authentication API
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="CumApp Auth Test", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "CumApp Auth Test API is running"}

@app.get("/test-imports")
async def test_imports():
    try:
        from database import get_db, check_database_connection
        from services.auth_service import AuthenticationService
        from api.auth_api import router
        
        db_status = check_database_connection()
        
        return {
            "status": "success",
            "imports": {
                "database": "OK",
                "auth_service": "OK", 
                "auth_api": "OK"
            },
            "database_connection": db_status
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

# Include auth API
try:
    from api.auth_api import router as auth_router
    app.include_router(auth_router)
    print("✅ Auth API router included")
except Exception as e:
    print(f"❌ Failed to include auth API: {e}")

if __name__ == "__main__":
    import uvicorn
    print("Starting simple test server on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")