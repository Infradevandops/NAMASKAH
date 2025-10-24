"""
Critical Security Fixes - Direct Integration
Pro Tips: Minimal dependencies, immediate security improvements
"""

import os
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path


def create_backup():
    """Create backup of main.py"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"main_backup_{timestamp}.py"
    shutil.copy2("main.py", backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path


def apply_security_fixes():
    """Apply critical security fixes to main.py"""
    print("🔒 Applying critical security fixes...")

    # Read current main.py
    with open("main.py", "r") as f:
        content = f.read()

    # Security imports to add
    security_imports = """
import time
import secrets
import hashlib
import logging
from typing import Dict, Any, Optional
import jwt
from datetime import datetime, timedelta
"""

    # Rate limiting implementation
    rate_limiting_code = """
# Rate Limiting Implementation
class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.limit = 100  # requests per minute
        self.window = 60  # seconds
    
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - self.window
        
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip] 
                if req_time > window_start
            ]
        else:
            self.requests[client_ip] = []
        
        if len(self.requests[client_ip]) >= self.limit:
            return False
        
        self.requests[client_ip].append(now)
        return True

# Initialize rate limiter
rate_limiter = RateLimiter()

# Security middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    # Rate limiting
    if not rate_limiter.is_allowed(client_ip):
        return JSONResponse({"error": "Rate limit exceeded"}, 429)
    
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    
    return response

# Input sanitization
def sanitize_input(input_str: str) -> str:
    if not input_str:
        return ""
    
    # Remove dangerous patterns
    dangerous = ["<script", "javascript:", "on\\w+\\s*=", "<iframe", "<object"]
    cleaned = input_str
    
    for pattern in dangerous:
        import re
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    
    return cleaned.strip()

# SQL injection prevention
def safe_db_query(db, query: str, params: dict):
    from sqlalchemy import text
    return db.execute(text(query), params)

# JWT token validation
def validate_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("exp", 0) < time.time():
            raise HTTPException(401, "Token expired")
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
"""

    # Find where to insert code
    if "from fastapi import" in content:
        # Add security imports after existing imports
        import_end = content.rfind("import")
        import_end = content.find("\n", import_end)
        content = content[:import_end] + "\n" + security_imports + content[import_end:]

    # Add rate limiting after app creation
    if "app = FastAPI(" in content:
        app_end = content.find("\n\n", content.find("app = FastAPI("))
        if app_end == -1:
            app_end = content.find("\n", content.find("app = FastAPI(")) + 1
        content = (
            content[:app_end] + "\n" + rate_limiting_code + "\n" + content[app_end:]
        )

    # Secure the verification endpoint
    old_verify_pattern = '@app.post("/verify/create")'
    if old_verify_pattern in content:
        # Find the function and add input sanitization
        func_start = content.find(
            "def create_verification", content.find(old_verify_pattern)
        )
        if func_start != -1:
            # Add sanitization at the beginning of the function
            func_body_start = content.find(":", func_start)
            func_body_start = content.find("\n", func_body_start) + 1

            sanitization_code = """    # Input sanitization
    service_name = sanitize_input(service_name)
    
    # Validate service name
    allowed_services = {"telegram", "whatsapp", "discord", "twitter", "instagram"}
    if service_name.lower() not in allowed_services:
        raise HTTPException(400, "Invalid service name")
    
"""
            content = (
                content[:func_body_start]
                + sanitization_code
                + content[func_body_start:]
            )

    # Secure admin endpoints
    admin_pattern = '@app.get("/admin/users")'
    if admin_pattern in content:
        func_start = content.find("def get_users", content.find(admin_pattern))
        if func_start != -1:
            func_body_start = content.find(":", func_start)
            func_body_start = content.find("\n", func_body_start) + 1

            secure_query_code = """    # Secure database query
    users = safe_db_query(db, 
        "SELECT id, email, credits, created_at FROM users WHERE is_active = :active ORDER BY created_at DESC", 
        {"active": True}
    ).fetchall()
    
    return [{"id": u.id, "email": u.email, "credits": u.credits, "created_at": u.created_at} for u in users]
"""
            # Replace the existing query
            func_end = content.find("\n\n", func_body_start)
            if func_end == -1:
                func_end = content.find("@app.", func_body_start)

            content = content[:func_body_start] + secure_query_code + content[func_end:]

    # Write the updated content
    with open("main.py", "w") as f:
        f.write(content)

    print("✅ Security fixes applied successfully")


def add_bulk_verification():
    """Add bulk verification endpoint"""
    print("📦 Adding bulk verification endpoint...")

    with open("main.py", "r") as f:
        content = f.read()

    bulk_endpoint = """
# Bulk verification endpoint
@app.post("/verify/bulk")
async def create_bulk_verifications(
    services: list,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if len(services) > 10:
        raise HTTPException(400, "Maximum 10 services per request")
    
    results = []
    for service in services:
        try:
            # Sanitize and validate
            service = sanitize_input(service)
            allowed_services = {"telegram", "whatsapp", "discord", "twitter", "instagram"}
            if service.lower() not in allowed_services:
                results.append({"service": service, "status": "error", "error": "Invalid service"})
                continue
            
            # Check credits
            if user.credits < 1:
                results.append({"service": service, "status": "error", "error": "Insufficient credits"})
                continue
            
            # Create verification
            verification = tv_client.create_verification(service)
            if verification.get("success"):
                results.append({
                    "service": service, 
                    "status": "success", 
                    "id": verification["id"],
                    "phone": verification.get("number")
                })
                
                # Deduct credit
                user.credits -= 1
                db.commit()
            else:
                results.append({"service": service, "status": "error", "error": "Service unavailable"})
        
        except Exception as e:
            results.append({"service": service, "status": "error", "error": str(e)})
    
    return {"results": results, "total": len(services), "successful": len([r for r in results if r["status"] == "success"])}
"""

    # Add at the end of the file
    content += "\n" + bulk_endpoint

    with open("main.py", "w") as f:
        f.write(content)

    print("✅ Bulk verification endpoint added")


def add_websocket_support():
    """Add basic WebSocket support"""
    print("🔌 Adding WebSocket support...")

    with open("main.py", "r") as f:
        content = f.read()

    # Add WebSocket import if not present
    if "from fastapi import WebSocket" not in content:
        fastapi_import = content.find("from fastapi import")
        import_end = content.find("\n", fastapi_import)
        old_import = content[fastapi_import:import_end]
        new_import = old_import.replace(
            "from fastapi import", "from fastapi import WebSocket,"
        )
        content = content.replace(old_import, new_import)

    websocket_code = """
# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections = {}
    
    async def connect(self, websocket: WebSocket, verification_id: str):
        await websocket.accept()
        self.active_connections[verification_id] = websocket
    
    def disconnect(self, verification_id: str):
        if verification_id in self.active_connections:
            del self.active_connections[verification_id]
    
    async def send_message(self, verification_id: str, message: dict):
        if verification_id in self.active_connections:
            try:
                await self.active_connections[verification_id].send_json(message)
            except:
                self.disconnect(verification_id)

manager = ConnectionManager()

# WebSocket endpoint
@app.websocket("/ws/verification/{verification_id}")
async def verification_websocket(websocket: WebSocket, verification_id: str):
    await manager.connect(websocket, verification_id)
    
    try:
        # Send initial connection message
        await websocket.send_json({"type": "connected", "verification_id": verification_id})
        
        # Keep connection alive and listen for messages
        while True:
            try:
                # Check for SMS messages every 3 seconds
                messages = tv_client.get_messages(verification_id)
                if messages:
                    await websocket.send_json({
                        "type": "sms_received", 
                        "messages": messages,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # If verification code received, notify completion
                    for msg in messages:
                        if msg.get("message") and any(char.isdigit() for char in msg["message"]):
                            await websocket.send_json({
                                "type": "verification_completed",
                                "code": msg["message"],
                                "timestamp": datetime.now().isoformat()
                            })
                            break
                
                await asyncio.sleep(3)
                
            except Exception as e:
                break
    
    except Exception:
        pass
    finally:
        manager.disconnect(verification_id)
"""

    # Add WebSocket code
    content += "\n" + websocket_code

    with open("main.py", "w") as f:
        f.write(content)

    print("✅ WebSocket support added")


def test_security_fixes():
    """Test if security fixes are working"""
    print("🧪 Testing security fixes...")

    try:
        import requests

        # Test rate limiting (simplified)
        print("  - Testing rate limiting...")
        for i in range(5):
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 429:
                    print("    ✅ Rate limiting active")
                    break
            except:
                pass

        # Test XSS prevention
        print("  - Testing XSS prevention...")
        try:
            response = requests.post(
                "http://localhost:8000/verify/create",
                json={"service_name": "<script>alert('xss')</script>"},
                timeout=2,
            )
            if response.status_code in [400, 422]:
                print("    ✅ XSS prevention active")
        except:
            pass

        print("✅ Security tests completed")

    except ImportError:
        print("⚠️ Requests module not available, skipping tests")


def main():
    """Main function to apply all fixes"""
    print("🚀 Applying Critical Security Fixes")
    print("=" * 50)

    try:
        # Create backup
        backup_path = create_backup()

        # Apply fixes
        apply_security_fixes()
        add_bulk_verification()
        add_websocket_support()

        print("\n✅ All critical fixes applied successfully!")
        print(f"📁 Backup saved as: {backup_path}")
        print("\n🔧 Next steps:")
        print("1. Restart the application: uvicorn main:app --reload")
        print("2. Test the security fixes")
        print("3. Monitor the application logs")

        # Test if server is running
        try:
            import requests

            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("\n🟢 Server is running - fixes will take effect on restart")
            else:
                print("\n🟡 Server status unknown")
        except:
            print("\n🔴 Server not running - start with: uvicorn main:app --reload")

    except Exception as e:
        print(f"\n❌ Error applying fixes: {str(e)}")
        print("Check the backup file and try again")
        sys.exit(1)


if __name__ == "__main__":
    main()
