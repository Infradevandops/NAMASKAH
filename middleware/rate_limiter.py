# Enhanced Per-User Rate Limiting
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
import jwt
from typing import Dict, Optional

class UserRateLimiter:
    def __init__(self):
        self.user_requests: Dict[str, list] = {}
        self.limits = {
            'starter': 100,    # requests per minute
            'pro': 500,
            'enterprise': 2000
        }
    
    def get_user_plan(self, request: Request) -> str:
        """Extract user plan from JWT token"""
        try:
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return 'starter'
            
            token = auth_header.split(" ")[1]
            # In production, decode JWT and get user plan from database
            # For now, return starter as default
            return 'starter'
        except:
            return 'starter'
    
    def is_allowed(self, user_id: str, plan: str) -> bool:
        """Check if user is within rate limits"""
        now = time.time()
        window_start = now - 60  # 1 minute window
        
        # Clean old requests
        if user_id in self.user_requests:
            self.user_requests[user_id] = [
                req_time for req_time in self.user_requests[user_id]
                if req_time > window_start
            ]
        else:
            self.user_requests[user_id] = []
        
        # Check limit
        limit = self.limits.get(plan, self.limits['starter'])
        if len(self.user_requests[user_id]) >= limit:
            return False
        
        # Add current request
        self.user_requests[user_id].append(now)
        return True
    
    def get_reset_time(self, user_id: str) -> int:
        """Get when rate limit resets"""
        if user_id not in self.user_requests or not self.user_requests[user_id]:
            return int(time.time())
        
        oldest_request = min(self.user_requests[user_id])
        return int(oldest_request + 60)

# Global rate limiter instance
rate_limiter = UserRateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware for API v2"""
    # Skip rate limiting for non-API routes
    if not request.url.path.startswith('/api/v2'):
        return await call_next(request)
    
    # Get user info
    user_id = request.client.host  # Fallback to IP
    plan = rate_limiter.get_user_plan(request)
    
    # Check rate limit
    if not rate_limiter.is_allowed(user_id, plan):
        reset_time = rate_limiter.get_reset_time(user_id)
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "limit": rate_limiter.limits[plan],
                "reset_at": reset_time,
                "retry_after": max(1, reset_time - int(time.time()))
            },
            headers={
                "X-RateLimit-Limit": str(rate_limiter.limits[plan]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(max(1, reset_time - int(time.time())))
            }
        )
    
    # Add rate limit headers to response
    response = await call_next(request)
    remaining = rate_limiter.limits[plan] - len(rate_limiter.user_requests.get(user_id, []))
    reset_time = rate_limiter.get_reset_time(user_id)
    
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.limits[plan])
    response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
    response.headers["X-RateLimit-Reset"] = str(reset_time)
    
    return response