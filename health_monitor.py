#!/usr/bin/env python3
"""
Health monitoring for SMSPROJ Platform
"""
import asyncio
import time
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class HealthMonitor:
    """System health monitoring"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.last_health_check = None
    
    def record_request(self):
        """Record a request"""
        self.request_count += 1
    
    def record_error(self):
        """Record an error"""
        self.error_count += 1
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        uptime = time.time() - self.start_time
        error_rate = (self.error_count / max(self.request_count, 1)) * 100
        
        status = {
            "status": "healthy" if error_rate < 5 else "degraded",
            "uptime_seconds": int(uptime),
            "uptime_human": self._format_uptime(uptime),
            "requests_total": self.request_count,
            "errors_total": self.error_count,
            "error_rate_percent": round(error_rate, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": {
                "database": True,  # Would check actual DB connection
                "redis": True,     # Would check actual Redis connection
                "external_apis": True  # Would check external services
            }
        }
        
        self.last_health_check = status
        return status
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

# Global health monitor
health_monitor = HealthMonitor()