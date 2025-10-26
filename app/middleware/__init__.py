"""Middleware package for cross-cutting concerns."""

# Security middleware
from .security import (
    JWTAuthMiddleware,
    APIKeyAuthMiddleware, 
    AdminRoleMiddleware,
    CORSMiddleware,
    SecurityHeadersMiddleware
)

# Rate limiting middleware
from .rate_limiting import (
    RateLimitMiddleware,
    AdaptiveRateLimitMiddleware
)

# Logging middleware
from .logging import (
    RequestLoggingMiddleware,
    PerformanceMetricsMiddleware,
    AuditTrailMiddleware
)

__all__ = [
    # Security
    "JWTAuthMiddleware",
    "APIKeyAuthMiddleware",
    "AdminRoleMiddleware", 
    "CORSMiddleware",
    "SecurityHeadersMiddleware",
    
    # Rate Limiting
    "RateLimitMiddleware",
    "AdaptiveRateLimitMiddleware",
    
    # Logging
    "RequestLoggingMiddleware",
    "PerformanceMetricsMiddleware",
    "AuditTrailMiddleware"
]