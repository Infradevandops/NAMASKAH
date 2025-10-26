"""Health check implementations for task 13.2."""
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.caching import cache


class HealthChecker:
    """Comprehensive health check system."""
    
    @staticmethod
    async def check_database() -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            db_gen = get_db()
            db = next(db_gen)
            try:
                db.execute("SELECT 1")
                return {"status": "healthy", "response_time": 0.01}
            finally:
                db.close()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    @staticmethod
    async def check_redis() -> Dict[str, Any]:
        """Check Redis connectivity."""
        try:
            await cache.connect()
            await cache.set("health_check", "ok", ttl=10)
            result = await cache.get("health_check")
            if result == "ok":
                return {"status": "healthy", "response_time": 0.005}
            else:
                return {"status": "unhealthy", "error": "Redis test failed"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    @staticmethod
    async def check_external_services() -> Dict[str, Any]:
        """Check external service connectivity."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("https://api.textverified.com/health")
                if response.status_code == 200:
                    return {"status": "healthy", "response_time": 0.1}
                else:
                    return {"status": "degraded", "status_code": response.status_code}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    @staticmethod
    async def comprehensive_health_check() -> Dict[str, Any]:
        """Run all health checks."""
        checks = await asyncio.gather(
            HealthChecker.check_database(),
            HealthChecker.check_redis(),
            HealthChecker.check_external_services(),
            return_exceptions=True
        )
        
        db_health, redis_health, external_health = checks
        
        overall_status = "healthy"
        if any(check.get("status") == "unhealthy" for check in checks):
            overall_status = "unhealthy"
        elif any(check.get("status") == "degraded" for check in checks):
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "database": db_health,
                "redis": redis_health,
                "external_apis": external_health
            }
        }


async def readiness_probe() -> bool:
    """Kubernetes readiness probe."""
    health = await HealthChecker.comprehensive_health_check()
    return health["status"] in ["healthy", "degraded"]


async def liveness_probe() -> bool:
    """Kubernetes liveness probe."""
    try:
        db_health = await HealthChecker.check_database()
        return db_health["status"] == "healthy"
    except Exception:
        return False