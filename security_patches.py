# Critical Security Patches - Rate Limiting, Input Validation, SQL Injection Prevention
import time
import re
import jwt
import hashlib
import hmac
import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory rate limiter
rate_limits = defaultdict(list)


def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware - 100 requests per minute per IP"""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Clean old requests (older than 60 seconds)
    rate_limits[client_ip] = [
        req_time for req_time in rate_limits[client_ip] if now - req_time < 60
    ]

    # Check limit (100 requests per minute)
    if len(rate_limits[client_ip]) >= 100:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return JSONResponse(
            {
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
            },
            status_code=429,
        )

    # Add current request
    rate_limits[client_ip].append(now)

    # Continue with request
    response = call_next(request)
    return response


def validate_service_name(service_name: str) -> str:
    """Validate and sanitize service name input"""
    if not service_name or not isinstance(service_name, str):
        raise HTTPException(status_code=400, detail="Service name is required")

    # Remove any potentially dangerous characters
    service_name = re.sub(r"[^a-zA-Z0-9_-]", "", service_name.lower().strip())

    # Check against whitelist of allowed services
    allowed_services = [
        "telegram",
        "whatsapp",
        "discord",
        "google",
        "instagram",
        "facebook",
        "twitter",
        "tiktok",
        "snapchat",
        "linkedin",
        "uber",
        "airbnb",
        "netflix",
        "spotify",
        "amazon",
        "microsoft",
        "apple",
        "yahoo",
        "outlook",
        "gmail",
        "signal",
        "viber",
        "line",
        "wechat",
        "skype",
        "zoom",
        "slack",
        "reddit",
        "pinterest",
        "tumblr",
        "twitch",
        "steam",
        "epic",
        "paypal",
        "coinbase",
        "binance",
        "kraken",
        "robinhood",
        "cashapp",
        "venmo",
        "zelle",
    ]

    if service_name not in allowed_services:
        # Allow it but log for monitoring
        logger.info(f"Unknown service requested: {service_name}")

    return service_name


def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False

    # Basic email regex
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_pattern, email.strip().lower()))


def sanitize_input(input_text: str) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if not isinstance(input_text, str):
        return str(input_text)

    # Remove potentially dangerous characters
    sanitized = input_text.strip()

    # Remove HTML tags
    sanitized = re.sub(r"<[^>]*>", "", sanitized)

    # Remove JavaScript protocols
    sanitized = re.sub(r"javascript:", "", sanitized, flags=re.IGNORECASE)

    # Remove SQL injection patterns
    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bOR\b.*=.*\bOR\b)",
        r"(\bAND\b.*=.*\bAND\b)",
        r"(\'|\"|;|\||&)",
    ]

    for pattern in sql_patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

    return sanitized[:1000]  # Limit length


def create_secure_token(user_id: str, secret_key: str, expires_hours: int = 24) -> str:
    """Create secure JWT token with proper expiration"""
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=expires_hours),
        "iat": datetime.now(timezone.utc),
        "iss": "namaskah-sms",
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def validate_token(token: str, secret_key: str) -> Optional[Dict[str, Any]]:
    """Validate JWT token and return payload if valid"""
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])

        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(
            timezone.utc
        ):
            return None

        return payload
    except jwt.InvalidTokenError:
        return None


def safe_query(db: Session, query_text: str, params: Dict[str, Any] = None) -> Any:
    """Execute parameterized query safely to prevent SQL injection"""
    try:
        if params:
            # Use parameterized query
            result = db.execute(text(query_text), params)
        else:
            result = db.execute(text(query_text))
        return result
    except Exception as e:
        logger.error(f"Database query error: {e}")
        raise HTTPException(status_code=500, detail="Database error")


def log_security_event(
    event_type: str, user_id: str = None, ip_address: str = None, details: str = None
):
    """Log security events for monitoring"""
    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = {
        "timestamp": timestamp,
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "details": details,
    }
    logger.warning(f"SECURITY EVENT: {log_entry}")


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature to prevent tampering"""
    try:
        expected_signature = hmac.new(
            secret.encode("utf-8"), payload, hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(signature, expected_signature)
    except Exception:
        return False


def hash_password_secure(password: str) -> str:
    """Securely hash password with bcrypt"""
    import bcrypt

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password_secure(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    import bcrypt

    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# Input validation schemas
class ValidationError(Exception):
    pass


def validate_verification_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate verification creation request"""
    validated = {}

    # Service name validation
    service_name = data.get("service_name", "").strip()
    if not service_name:
        raise ValidationError("Service name is required")
    validated["service_name"] = validate_service_name(service_name)

    # Capability validation
    capability = data.get("capability", "sms").strip().lower()
    if capability not in ["sms", "voice"]:
        raise ValidationError("Invalid capability. Must be 'sms' or 'voice'")
    validated["capability"] = capability

    # Area code validation (optional)
    area_code = data.get("area_code")
    if area_code:
        area_code = re.sub(r"[^0-9]", "", str(area_code))
        if len(area_code) != 3:
            raise ValidationError("Area code must be 3 digits")
        validated["area_code"] = area_code

    # Carrier validation (optional)
    carrier = data.get("carrier")
    if carrier:
        carrier = re.sub(r"[^a-zA-Z0-9_-]", "", str(carrier).lower())
        allowed_carriers = ["verizon", "att", "tmobile", "sprint"]
        if carrier not in allowed_carriers:
            raise ValidationError(
                f"Invalid carrier. Must be one of: {', '.join(allowed_carriers)}"
            )
        validated["carrier"] = carrier

    return validated


def validate_user_registration(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user registration data"""
    validated = {}

    # Email validation
    email = data.get("email", "").strip().lower()
    if not validate_email(email):
        raise ValidationError("Invalid email format")
    validated["email"] = email

    # Password validation
    password = data.get("password", "")
    if len(password) < 6:
        raise ValidationError("Password must be at least 6 characters")
    if len(password) > 128:
        raise ValidationError("Password too long")

    # Check for common weak passwords
    weak_passwords = ["123456", "password", "123456789", "qwerty", "abc123"]
    if password.lower() in weak_passwords:
        raise ValidationError("Password is too weak")

    validated["password"] = password

    return validated


# Security headers middleware
def add_security_headers(response):
    """Add security headers to response"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline' https://accounts.google.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' wss: https:;"
    )
    return response


# Request size limiter
def validate_request_size(request: Request, max_size: int = 1024 * 1024):  # 1MB default
    """Validate request size to prevent DoS attacks"""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > max_size:
        raise HTTPException(status_code=413, detail="Request too large")


# IP whitelist/blacklist
BLOCKED_IPS = set()
ALLOWED_IPS = set()  # Empty means all IPs allowed


def check_ip_access(ip: str) -> bool:
    """Check if IP is allowed access"""
    if ip in BLOCKED_IPS:
        return False

    if ALLOWED_IPS and ip not in ALLOWED_IPS:
        return False

    return True


def block_ip(ip: str, reason: str = "Security violation"):
    """Block an IP address"""
    BLOCKED_IPS.add(ip)
    log_security_event("ip_blocked", ip_address=ip, details=reason)


# Session management
active_sessions = {}


def create_session(user_id: str, ip: str) -> str:
    """Create secure session"""
    import secrets

    session_id = secrets.token_urlsafe(32)
    active_sessions[session_id] = {
        "user_id": user_id,
        "ip": ip,
        "created_at": datetime.now(timezone.utc),
        "last_activity": datetime.now(timezone.utc),
    }
    return session_id


def validate_session(session_id: str, ip: str) -> Optional[str]:
    """Validate session and return user_id if valid"""
    session = active_sessions.get(session_id)
    if not session:
        return None

    # Check IP consistency
    if session["ip"] != ip:
        log_security_event("session_ip_mismatch", session["user_id"], ip)
        return None

    # Check session age (24 hours max)
    if datetime.now(timezone.utc) - session["created_at"] > timedelta(hours=24):
        del active_sessions[session_id]
        return None

    # Update last activity
    session["last_activity"] = datetime.now(timezone.utc)
    return session["user_id"]


def invalidate_session(session_id: str):
    """Invalidate a session"""
    if session_id in active_sessions:
        del active_sessions[session_id]


# Export all security functions
__all__ = [
    "rate_limit_middleware",
    "validate_service_name",
    "validate_email",
    "sanitize_input",
    "create_secure_token",
    "validate_token",
    "safe_query",
    "log_security_event",
    "verify_webhook_signature",
    "hash_password_secure",
    "verify_password_secure",
    "validate_verification_request",
    "validate_user_registration",
    "add_security_headers",
    "validate_request_size",
    "check_ip_access",
    "block_ip",
    "create_session",
    "validate_session",
    "invalidate_session",
]
