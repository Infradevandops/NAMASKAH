"""Security utilities for input validation and protection"""

import re
import bleach
from typing import Optional
from passlib.context import CryptContext
from datetime import datetime, timedelta
import secrets

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password securely"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Password is valid"


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS"""
    if not text:
        return ""
    # Remove HTML tags and dangerous characters
    cleaned = bleach.clean(text, tags=[], strip=True)
    return cleaned.strip()


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def generate_secure_token() -> str:
    """Generate cryptographically secure token"""
    return secrets.token_urlsafe(32)


def is_safe_redirect_url(url: str, allowed_hosts: list) -> bool:
    """Check if redirect URL is safe"""
    if not url:
        return False

    # Check for relative URLs (safe)
    if url.startswith("/") and not url.startswith("//"):
        return True

    # Check against allowed hosts
    for host in allowed_hosts:
        if url.startswith(f"https://{host}") or url.startswith(f"http://{host}"):
            return True

    return False


class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        self.attempts = {}

    def is_allowed(
        self, key: str, max_attempts: int = 5, window_minutes: int = 15
    ) -> bool:
        """Check if request is allowed based on rate limit"""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)

        # Clean old entries
        self.attempts = {
            k: v
            for k, v in self.attempts.items()
            if any(attempt > window_start for attempt in v)
        }

        # Check current attempts
        if key not in self.attempts:
            self.attempts[key] = []

        # Remove old attempts for this key
        self.attempts[key] = [
            attempt for attempt in self.attempts[key] if attempt > window_start
        ]

        # Check if limit exceeded
        if len(self.attempts[key]) >= max_attempts:
            return False

        # Add current attempt
        self.attempts[key].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()
