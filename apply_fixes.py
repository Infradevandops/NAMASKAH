#!/usr/bin/env python3
"""
Apply Critical Security and Performance Fixes
Run this script to patch the main application with urgent fixes
"""

import os
import shutil
from datetime import datetime

def backup_main_file():
    """Create backup of main.py before applying fixes"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"main_backup_{timestamp}.py"
    shutil.copy("main.py", backup_name)
    print(f"✅ Backup created: {backup_name}")

def apply_security_patches():
    """Apply security patches to main.py"""
    
    # Read current main.py
    with open("main.py", "r") as f:
        content = f.read()
    
    # 1. Add security imports at top
    security_imports = """
# Security patches
from security_patches import (
    rate_limit_middleware, validate_service_name, validate_email,
    sanitize_input, create_secure_token, validate_token,
    safe_query, log_security_event, verify_webhook_signature,
    hash_password_secure, verify_password_secure
)
"""
    
    # Insert after existing imports
    import_pos = content.find("from fastapi import FastAPI")
    if import_pos != -1:
        content = content[:import_pos] + security_imports + "\n" + content[import_pos:]
    
    # 2. Add rate limiting middleware
    middleware_code = """
# Add security middleware
app.add_middleware(rate_limit_middleware)
"""
    
    # Insert after app creation
    app_pos = content.find("app = FastAPI(")
    if app_pos != -1:
        # Find end of FastAPI constructor
        end_pos = content.find(")", app_pos)
        end_pos = content.find("\n", end_pos)
        content = content[:end_pos] + "\n" + middleware_code + content[end_pos:]
    
    # 3. Update verification endpoint with validation
    old_verification = """def create_verification(req: CreateVerificationRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):"""
    
    new_verification = """def create_verification(req: CreateVerificationRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Validate input
    req.service_name = validate_service_name(req.service_name)
    
    # Log security event
    log_security_event("verification_create", user.id, details=f"Service: {req.service_name}")"""
    
    content = content.replace(old_verification, new_verification)
    
    # 4. Update login endpoint with secure password verification
    old_login = """if not user or not bcrypt.checkpw(req.password.encode(), user.password_hash.encode()):"""
    new_login = """if not user or not verify_password_secure(req.password, user.password_hash):"""
    
    content = content.replace(old_login, new_login)
    
    # 5. Update registration with secure password hashing
    old_register = """password_hash=bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode(),"""
    new_register = """password_hash=hash_password_secure(req.password),"""
    
    content = content.replace(old_register, new_register)
    
    # Write updated content
    with open("main.py", "w") as f:
        f.write(content)
    
    print("✅ Security patches applied to main.py")

def add_websocket_support():
    """Add WebSocket support to main.py"""
    
    with open("main.py", "r") as f:
        content = f.read()
    
    # Add WebSocket import
    websocket_import = """
# WebSocket support
from websocket_realtime import add_websocket_routes
"""
    
    # Insert after security imports
    import_pos = content.find("from security_patches import")
    if import_pos != -1:
        end_pos = content.find("\n)", import_pos)
        end_pos = content.find("\n", end_pos)
        content = content[:end_pos] + websocket_import + content[end_pos:]
    
    # Add WebSocket routes at end of file
    websocket_setup = """
# Add WebSocket routes
add_websocket_routes(app, tv_client, SessionLocal)
"""
    
    content += websocket_setup
    
    with open("main.py", "w") as f:
        f.write(content)
    
    print("✅ WebSocket support added")

def update_frontend_with_websocket():
    """Update minimal dashboard with WebSocket client"""
    
    with open("templates/dashboard.html", "r") as f:
        content = f.read()
    
    # Add WebSocket client script
    websocket_script = """
    <script src="/ws/client.js"></script>
    <script>
        // Override createVerification to use WebSocket
        const originalCreateVerification = window.createVerification;
        window.createVerification = async function(serviceName) {
            const result = await originalCreateVerification(serviceName);
            if (result && result.id) {
                startRealtimeMonitoring(result.id);
            }
            return result;
        };
    </script>
"""
    
    # Insert before closing body tag
    body_end = content.rfind("</body>")
    if body_end != -1:
        content = content[:body_end] + websocket_script + content[body_end:]
    
    with open("templates/dashboard.html", "w") as f:
        f.write(content)
    
    print("✅ Frontend updated with WebSocket support")

def create_requirements_update():
    """Create updated requirements with security dependencies"""
    
    security_deps = """
# Security and WebSocket dependencies
bcrypt>=4.0.0
python-jose[cryptography]>=3.3.0
websockets>=11.0.0
httpx>=0.24.0
redis>=4.5.0
"""
    
    with open("requirements_security.txt", "w") as f:
        f.write(security_deps)
    
    print("✅ Security requirements created: requirements_security.txt")

def main():
    """Apply all fixes"""
    print("🚨 Applying Critical Security and Performance Fixes...")
    print("=" * 50)
    
    # Create backup
    backup_main_file()
    
    # Apply fixes
    apply_security_patches()
    add_websocket_support()
    update_frontend_with_websocket()
    create_requirements_update()
    
    print("\n" + "=" * 50)
    print("✅ All fixes applied successfully!")
    print("\n📋 Next Steps:")
    print("1. Install security dependencies: pip install -r requirements_security.txt")
    print("2. Restart the server: uvicorn main:app --reload")
    print("3. Test at: http://localhost:8000/simple")
    print("4. Monitor logs for security events")
    print("\n⚠️  If issues occur, restore from backup file")

if __name__ == "__main__":
    main()