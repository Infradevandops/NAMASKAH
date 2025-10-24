"""
Minimal Security Fixes - Clean Implementation
"""
import os
import shutil
from datetime import datetime

def create_backup():
    """Create backup of main.py"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"main_backup_minimal_{timestamp}.py"
    shutil.copy2("main.py", backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def apply_minimal_fixes():
    """Apply minimal security fixes without breaking syntax"""
    print("🔒 Applying minimal security fixes...")
    
    # Read current main.py
    with open("main.py", "r") as f:
        content = f.read()
    
    # Add minimal security imports after existing imports
    security_imports = '''
import time
import secrets
import hashlib
import logging
from typing import Dict, Any, Optional
'''
    
    # Find the last import and add security imports
    import_lines = []
    other_lines = []
    in_imports = True
    
    for line in content.split('\n'):
        if in_imports and (line.startswith('import ') or line.startswith('from ') or line.strip() == ''):
            import_lines.append(line)
        else:
            if in_imports and line.strip():
                in_imports = False
            other_lines.append(line)
    
    # Add security imports
    import_lines.extend(security_imports.strip().split('\n'))
    
    # Add minimal rate limiting class
    rate_limiting_code = '''
# Minimal Rate Limiting
class SimpleRateLimiter:
    def __init__(self):
        self.requests = {}
        self.limit = 100
        self.window = 60
    
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
rate_limiter = SimpleRateLimiter()

# Input sanitization
def sanitize_input(input_str: str) -> str:
    if not input_str:
        return ""
    
    import re
    # Remove dangerous patterns
    dangerous = [r"<script[^>]*>.*?</script>", r"javascript:", r"on\\w+\\s*="]
    cleaned = input_str
    
    for pattern in dangerous:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)
    
    return cleaned.strip()
'''
    
    # Combine all content
    new_content = '\n'.join(import_lines) + '\n\n' + rate_limiting_code + '\n\n' + '\n'.join(other_lines)
    
    # Add security middleware before app routes
    if 'app = FastAPI(' in new_content:
        app_index = new_content.find('app = FastAPI(')
        # Find the end of the FastAPI initialization
        app_end = new_content.find('\n\n', app_index)
        if app_end == -1:
            app_end = new_content.find('\n', app_index) + 1
        
        middleware_code = '''
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
    
    return response
'''
        
        new_content = new_content[:app_end] + '\n' + middleware_code + new_content[app_end:]
    
    # Write the updated content
    with open("main.py", "w") as f:
        f.write(new_content)
    
    print("✅ Minimal security fixes applied successfully")

def main():
    """Main function"""
    print("🚀 Applying Minimal Security Fixes")
    print("=" * 40)
    
    try:
        # Create backup
        backup_path = create_backup()
        
        # Apply fixes
        apply_minimal_fixes()
        
        print("\n✅ Minimal fixes applied successfully!")
        print(f"📁 Backup saved as: {backup_path}")
        print("\n🔧 Next steps:")
        print("1. Restart the application: uvicorn main:app --reload")
        print("2. Test the application")
        
    except Exception as e:
        print(f"\n❌ Error applying fixes: {str(e)}")

if __name__ == "__main__":
    main()