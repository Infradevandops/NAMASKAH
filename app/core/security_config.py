"""Security configuration and utilities."""

import os
import secrets
from typing import List, Dict, Any
from app.core.config import get_settings


class SecurityConfig:
    """Security configuration management."""

    # Sensitive data patterns to redact from logs
    SENSITIVE_PATTERNS = [
        "password",
        "token",
        "secret",
        "key",
        "api_key",
        "auth_token",
        "bearer",
        "authorization",
        "credit_card",
        "ssn",
        "social_security",
        "private_key",
        "certificate",
        "credentials",
        "session_id",
    ]

    # Headers that should be redacted in logs
    SENSITIVE_HEADERS = [
        "authorization",
        "x-api-key",
        "cookie",
        "x-auth-token",
        "bearer",
        "x-session-id",
        "x-csrf-token",
    ]

    # Query parameters that should be redacted
    SENSITIVE_PARAMS = [
        "password",
        "token",
        "key",
        "secret",
        "api_key",
        "auth",
        "session",
        "csrf",
        "signature",
    ]

    # Allowed hosts for production (prevent host header injection)
    ALLOWED_HOSTS = [
        "namaskah.onrender.com",
        "api.namaskah.com",
        "localhost",
        "127.0.0.1",
    ]

    # Security headers to add to responses
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
    }

    @classmethod
    def is_sensitive_key(cls, key: str) -> bool:
        """Check if a key contains sensitive information."""
        key_lower = key.lower()
        return any(pattern in key_lower for pattern in cls.SENSITIVE_PATTERNS)

    @classmethod
    def sanitize_data(cls, data: Any) -> Any:
        """Recursively sanitize sensitive data."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if cls.is_sensitive_key(key):
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, (dict, list)):
                    sanitized[key] = cls.sanitize_data(value)
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [cls.sanitize_data(item) for item in data]
        else:
            return data

    @classmethod
    def validate_host(cls, host: str) -> bool:
        """Validate if host is allowed."""
        settings = get_settings()
        if settings.environment == "development":
            return True  # Allow all hosts in development

        return host in cls.ALLOWED_HOSTS

    @classmethod
    def generate_secure_token(cls, length: int = 32) -> str:
        """Generate a cryptographically secure token."""
        return secrets.token_urlsafe(length)

    @classmethod
    def validate_input_length(cls, value: str, max_length: int = 1000) -> bool:
        """Validate input length to prevent DoS attacks."""
        return len(value) <= max_length

    @classmethod
    def get_safe_filename(cls, filename: str) -> str:
        """Get a safe filename by removing dangerous characters."""
        import re

        # Remove path traversal attempts and dangerous characters
        safe_name = re.sub(r"[^\w\-_\.]", "", filename)
        # Limit length
        return safe_name[:100]

    @classmethod
    def validate_sql_identifier(cls, identifier: str) -> bool:
        """Validate SQL identifier to prevent injection."""
        import re

        # Only allow alphanumeric characters and underscores
        return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", identifier))


class RateLimitConfig:
    """Rate limiting configuration."""

    # Default rate limits (requests per minute)
    DEFAULT_LIMITS = {
        "auth": 5,  # Login/register attempts
        "verification": 10,  # SMS verification requests
        "api": 60,  # General API calls
        "webhook": 100,  # Webhook deliveries
    }

    # Burst limits (maximum requests in short period)
    BURST_LIMITS = {"auth": 10, "verification": 20, "api": 120, "webhook": 200}

    # Lockout durations (minutes)
    LOCKOUT_DURATIONS = {
        "auth": 15,  # 15 minutes for failed auth
        "verification": 5,  # 5 minutes for verification spam
        "api": 1,  # 1 minute for API abuse
        "webhook": 1,  # 1 minute for webhook spam
    }


class AuditConfig:
    """Audit logging configuration."""

    # Events that require audit logging
    AUDIT_EVENTS = [
        "user_login",
        "user_logout",
        "user_register",
        "password_change",
        "api_key_create",
        "api_key_delete",
        "verification_create",
        "payment_process",
        "admin_action",
        "webhook_create",
        "webhook_delete",
        "settings_change",
    ]

    # Sensitive operations that require enhanced logging
    SENSITIVE_OPERATIONS = [
        "admin_login",
        "user_delete",
        "payment_refund",
        "api_key_regenerate",
        "webhook_secret_change",
    ]

    @classmethod
    def should_audit(cls, operation: str) -> bool:
        """Check if operation should be audited."""
        return operation in cls.AUDIT_EVENTS

    @classmethod
    def is_sensitive_operation(cls, operation: str) -> bool:
        """Check if operation is sensitive and needs enhanced logging."""
        return operation in cls.SENSITIVE_OPERATIONS
