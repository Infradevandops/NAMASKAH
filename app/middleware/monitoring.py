"""Monitoring middleware for request tracking."""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.monitoring import performance_monitor, error_tracker


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to track request metrics and errors."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and track metrics."""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Track request metrics
            await performance_monitor.track_request(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                duration=duration
            )
            
            # Add monitoring headers
            response.headers["X-Response-Time"] = str(duration)
            
            return response
            
        except Exception as e:
            # Track error
            error_tracker.track_error(e, {
                "endpoint": request.url.path,
                "method": request.method,
                "user_agent": request.headers.get("user-agent"),
                "ip": request.client.host if request.client else None
            })
            
            # Re-raise the exception
            raise