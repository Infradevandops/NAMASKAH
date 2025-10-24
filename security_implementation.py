"""
PHASE 1: Critical Security Implementation
Pro Tips: Defense in depth, fail-safe defaults, least privilege
"""
import time
import secrets
import hashlib
import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta

# Pro Tip: Centralized security configuration
class SecurityConfig:
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 60  # seconds
    JWT_EXPIRY_HOURS = 24
    CSRF_TOKEN_LENGTH = 32
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 300  # 5 minutes

# Pro Tip: In-memory rate limiting with sliding window
class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - SecurityConfig.RATE_LIMIT_WINDOW
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip] 
                if req_time > window_start
            ]
        else:
            self.requests[client_ip] = []
        
        # Check limit
        if len(self.requests[client_ip]) >= SecurityConfig.RATE_LIMIT_REQUESTS:
            return False
        
        # Add current request
        self.requests[client_ip].append(now)
        return True

# Pro Tip: CSRF token management with secure generation
class CSRFManager:
    def __init__(self):
        self.tokens: Dict[str, float] = {}
    
    def generate_token(self, session_id: str) -> str:
        token = secrets.token_urlsafe(SecurityConfig.CSRF_TOKEN_LENGTH)
        self.tokens[token] = time.time() + 3600  # 1 hour expiry
        return token
    
    def validate_token(self, token: str) -> bool:
        if token not in self.tokens:
            return False
        
        if time.time() > self.tokens[token]:
            del self.tokens[token]
            return False
        
        return True
    
    def cleanup_expired(self):
        now = time.time()
        expired = [token for token, expiry in self.tokens.items() if now > expiry]
        for token in expired:
            del self.tokens[token]

# Pro Tip: Secure JWT handling with proper validation
class JWTManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def create_token(self, user_id: str, email: str) -> str:
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": datetime.utcnow() + timedelta(hours=SecurityConfig.JWT_EXPIRY_HOURS),
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16)  # JWT ID for revocation
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # Pro Tip: Additional security checks
            if payload.get("exp", 0) < time.time():
                raise HTTPException(401, "Token expired")
            
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(401, "Invalid token")

# Pro Tip: SQL injection prevention with parameterized queries
class SecureDatabase:
    @staticmethod
    def safe_user_query(db: Session, email: str):
        """Prevent SQL injection in user queries"""
        return db.execute(
            text("SELECT * FROM users WHERE email = :email AND is_active = :active"),
            {"email": email, "active": True}
        ).first()
    
    @staticmethod
    def safe_admin_stats(db: Session, date_from: str, date_to: str):
        """Secure admin statistics query"""
        return db.execute(
            text("""
                SELECT COUNT(*) as total_users, 
                       SUM(credits) as total_credits,
                       COUNT(CASE WHEN created_at >= :date_from THEN 1 END) as new_users
                FROM users 
                WHERE created_at BETWEEN :date_from AND :date_to
            """),
            {"date_from": date_from, "date_to": date_to}
        ).first()
    
    @staticmethod
    def safe_verification_lookup(db: Session, verification_id: str, user_id: str):
        """Secure verification access with user ownership check"""
        return db.execute(
            text("""
                SELECT v.* FROM verifications v 
                WHERE v.id = :verification_id 
                AND v.user_id = :user_id
            """),
            {"verification_id": verification_id, "user_id": user_id}
        ).first()

# Pro Tip: Input sanitization with comprehensive validation
class InputSanitizer:
    @staticmethod
    def sanitize_html(input_str: str) -> str:
        """Remove HTML/JS injection attempts"""
        if not input_str:
            return ""
        
        # Remove script tags and event handlers
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>'
        ]
        
        import re
        cleaned = input_str
        for pattern in dangerous_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        
        return cleaned.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Strict email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) and len(email) <= 254
    
    @staticmethod
    def validate_service_name(service: str) -> bool:
        """Validate service name against whitelist"""
        allowed_services = {
            'telegram', 'whatsapp', 'discord', 'twitter', 'instagram',
            'facebook', 'tiktok', 'snapchat', 'linkedin', 'gmail'
        }
        return service.lower() in allowed_services

# Pro Tip: Comprehensive security middleware
async def security_middleware(request: Request, call_next):
    """
    Multi-layer security middleware
    Best Practice: Fail fast, log everything, provide minimal error info
    """
    start_time = time.time()
    client_ip = request.client.host
    
    try:
        # Rate limiting check
        if not rate_limiter.is_allowed(client_ip):
            logging.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                {"error": "Too many requests", "retry_after": 60}, 
                status_code=429
            )
        
        # CSRF protection for state-changing operations
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            csrf_token = request.headers.get("X-CSRF-Token")
            if not csrf_token or not csrf_manager.validate_token(csrf_token):
                logging.warning(f"CSRF token validation failed for IP: {client_ip}")
                return JSONResponse(
                    {"error": "CSRF token required"}, 
                    status_code=403
                )
        
        # Security headers
        response = await call_next(request)
        
        # Pro Tip: Comprehensive security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:"
        )
        
        # Log successful requests
        process_time = time.time() - start_time
        logging.info(f"Request processed: {request.method} {request.url.path} - {process_time:.3f}s")
        
        return response
        
    except Exception as e:
        logging.error(f"Security middleware error: {str(e)}")
        return JSONResponse(
            {"error": "Internal security error"}, 
            status_code=500
        )

# Pro Tip: Brute force protection
class BruteForceProtection:
    def __init__(self):
        self.failed_attempts: Dict[str, list] = {}
        self.locked_accounts: Dict[str, float] = {}
    
    def record_failed_attempt(self, identifier: str):
        """Record failed login attempt"""
        now = time.time()
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        # Clean old attempts (last 15 minutes)
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if now - attempt < 900
        ]
        
        self.failed_attempts[identifier].append(now)
        
        # Lock account if too many attempts
        if len(self.failed_attempts[identifier]) >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
            self.locked_accounts[identifier] = now + SecurityConfig.LOCKOUT_DURATION
            logging.warning(f"Account locked due to brute force: {identifier}")
    
    def is_locked(self, identifier: str) -> bool:
        """Check if account is locked"""
        if identifier in self.locked_accounts:
            if time.time() < self.locked_accounts[identifier]:
                return True
            else:
                del self.locked_accounts[identifier]
        return False
    
    def clear_attempts(self, identifier: str):
        """Clear failed attempts on successful login"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
        if identifier in self.locked_accounts:
            del self.locked_accounts[identifier]

# Initialize security components
rate_limiter = RateLimiter()
csrf_manager = CSRFManager()
brute_force_protection = BruteForceProtection()

# Pro Tip: Security event logging
def setup_security_logging():
    """Configure security-focused logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('security.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create security logger
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.WARNING)
    
    return security_logger

# Initialize security logging
security_logger = setup_security_logging()