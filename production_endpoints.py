"""
Production monitoring endpoints - Minimal implementation
"""

from fastapi import Request, HTTPException
from datetime import datetime, timezone
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage (use Redis in production)
metrics_store = []
error_store = []

@app.post("/api/metrics", tags=["Production"], summary="Log Performance Metrics")
async def log_metrics(request: Request):
    """Log performance metrics from frontend"""
    try:
        data = await request.json()
        
        metric = {
            "type": data.get("type"),
            "data": data.get("data"),
            "timestamp": data.get("timestamp", datetime.now(timezone.utc).timestamp() * 1000),
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        metrics_store.append(metric)
        
        # Keep only last 1000 metrics
        if len(metrics_store) > 1000:
            metrics_store.pop(0)
        
        # Log critical metrics
        if data.get("type") in ["slow_api", "error"]:
            logger.warning(f"Performance issue: {metric}")
        
        return {"status": "logged"}
    except Exception as e:
        logger.error(f"Metrics logging failed: {e}")
        return {"status": "error"}

@app.post("/api/errors", tags=["Production"], summary="Log Frontend Errors")
async def log_errors(request: Request):
    """Log frontend errors for monitoring"""
    try:
        data = await request.json()
        
        error = {
            "type": data.get("type"),
            "message": data.get("message"),
            "filename": data.get("filename"),
            "line": data.get("line"),
            "stack": data.get("stack"),
            "timestamp": data.get("timestamp", datetime.now(timezone.utc).timestamp() * 1000),
            "url": data.get("url"),
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        error_store.append(error)
        
        # Keep only last 500 errors
        if len(error_store) > 500:
            error_store.pop(0)
        
        # Log all errors
        logger.error(f"Frontend error: {error}")
        
        return {"status": "logged"}
    except Exception as e:
        logger.error(f"Error logging failed: {e}")
        return {"status": "error"}

@app.get("/admin/production/metrics", tags=["Admin"], summary="Get Production Metrics")
def get_production_metrics(admin: User = Depends(get_admin_user)):
    """Get production performance metrics (admin only)"""
    
    # Calculate basic stats
    total_metrics = len(metrics_store)
    error_count = len([m for m in metrics_store if m["type"] == "error"])
    slow_api_count = len([m for m in metrics_store if m["type"] == "slow_api"])
    
    # Recent metrics (last hour)
    one_hour_ago = (datetime.now(timezone.utc).timestamp() - 3600) * 1000
    recent_metrics = [m for m in metrics_store if m["timestamp"] > one_hour_ago]
    
    return {
        "total_metrics": total_metrics,
        "error_count": error_count,
        "slow_api_count": slow_api_count,
        "recent_metrics": len(recent_metrics),
        "recent_errors": len([m for m in recent_metrics if m["type"] == "error"]),
        "metrics": metrics_store[-50:],  # Last 50 metrics
        "errors": error_store[-20:]      # Last 20 errors
    }

@app.get("/admin/production/health", tags=["Admin"], summary="Production Health Check")
def production_health_check(admin: User = Depends(get_admin_user)):
    """Comprehensive production health check"""
    
    # Check database
    db_healthy = True
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except:
        db_healthy = False
    
    # Check TextVerified API
    tv_healthy = True
    try:
        tv_client.get_token()
    except:
        tv_healthy = False
    
    # Check error rates
    recent_errors = len([e for e in error_store if e["timestamp"] > (datetime.now(timezone.utc).timestamp() - 3600) * 1000])
    error_rate_ok = recent_errors < 10  # Less than 10 errors per hour
    
    overall_health = "healthy" if all([db_healthy, tv_healthy, error_rate_ok]) else "degraded"
    
    return {
        "status": overall_health,
        "database": "healthy" if db_healthy else "error",
        "textverified_api": "healthy" if tv_healthy else "error",
        "error_rate": "ok" if error_rate_ok else "high",
        "recent_errors": recent_errors,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/admin/production/clear-logs", tags=["Admin"], summary="Clear Production Logs")
def clear_production_logs(admin: User = Depends(get_admin_user)):
    """Clear production metrics and error logs"""
    global metrics_store, error_store
    
    metrics_count = len(metrics_store)
    errors_count = len(error_store)
    
    metrics_store.clear()
    error_store.clear()
    
    return {
        "message": "Logs cleared",
        "cleared_metrics": metrics_count,
        "cleared_errors": errors_count
    }