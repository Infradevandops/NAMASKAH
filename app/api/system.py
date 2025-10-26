"""System API router for health checks and service status."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.health_checks import HealthChecker, readiness_probe, liveness_probe
from app.core.monitoring import dashboard_metrics
from app.schemas import HealthCheck, ServiceStatusSummary, ServiceStatus

router = APIRouter(prefix="/system", tags=["System"])

# Add a root router for landing page
root_router = APIRouter()


@router.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    return await HealthChecker.comprehensive_health_check()


@router.get("/health/readiness")
async def readiness_check():
    """Kubernetes readiness probe."""
    from fastapi.responses import JSONResponse

    is_ready = await readiness_probe()
    status_code = 200 if is_ready else 503
    return JSONResponse(status_code=status_code, content={"ready": is_ready})


@router.get("/health/liveness")
async def liveness_check():
    """Kubernetes liveness probe."""
    from fastapi.responses import JSONResponse

    is_alive = await liveness_probe()
    status_code = 200 if is_alive else 503
    return JSONResponse(status_code=status_code, content={"alive": is_alive})


@router.get("/status", response_model=ServiceStatusSummary)
def get_service_status(db: Session = Depends(get_db)):
    """Get comprehensive service status."""
    from app.models.system import ServiceStatus as ServiceStatusModel

    # Get service statuses from database
    services = db.query(ServiceStatusModel).all()

    # Convert to response format
    service_statuses = [
        ServiceStatus(
            service_name=service.service_name,
            status=service.status,
            success_rate=service.success_rate,
            last_checked=service.last_checked,
        )
        for service in services
    ]

    # Calculate overall status
    if not service_statuses:
        overall_status = "unknown"
        stats = {"operational": 0, "degraded": 0, "down": 0}
    else:
        status_counts = {}
        for service in service_statuses:
            status_counts[service.status] = status_counts.get(service.status, 0) + 1

        if status_counts.get("down", 0) > 0:
            overall_status = "down"
        elif status_counts.get("degraded", 0) > 0:
            overall_status = "degraded"
        else:
            overall_status = "operational"

        stats = {
            "operational": status_counts.get("operational", 0),
            "degraded": status_counts.get("degraded", 0),
            "down": status_counts.get("down", 0),
        }

    return ServiceStatusSummary(
        overall_status=overall_status,
        services=service_statuses,
        stats=stats,
        last_updated=datetime.now(timezone.utc),
    )


@router.get("/info")
def get_system_info():
    """Get basic system information."""
    return {
        "service_name": "Namaskah SMS",
        "version": "2.3.0",
        "environment": getattr(settings, "environment", "production"),
        "features": {
            "sms_verification": True,
            "payment_processing": True,
            "admin_panel": True,
            "analytics": True,
        },
        "limits": {
            "max_concurrent_verifications": 100,
            "rate_limit_per_minute": 60,
            "max_api_keys_per_user": 5,
        },
    }


@router.get("/config")
def get_public_config():
    """Get public configuration settings."""
    return {
        "supported_services": [
            "telegram",
            "whatsapp",
            "discord",
            "instagram",
            "twitter",
            "facebook",
            "google",
            "microsoft",
        ],
        "payment_methods": ["paystack"],
        "currencies": ["NGN"],
        "min_credit_amount": 100.0,
        "verification_timeout_minutes": 10,
        "api_version": "v1",
    }


@router.get("/metrics")
async def get_system_metrics():
    """Get system performance metrics."""
    return await dashboard_metrics.get_system_health()


@router.get("/metrics/business")
async def get_business_metrics():
    """Get business metrics."""
    return await dashboard_metrics.get_business_metrics()


@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """Get Prometheus-formatted metrics."""
    from app.core.metrics import get_prometheus_metrics, get_metrics_content_type
    from fastapi.responses import Response

    metrics_data = get_prometheus_metrics()
    return Response(content=metrics_data, media_type=get_metrics_content_type())


@router.get("/metrics/application")
async def get_application_metrics():
    """Get application-specific metrics."""
    from app.core.metrics import metrics_collector

    app_metrics = metrics_collector.get_application_metrics()
    health_score = metrics_collector.get_health_score()

    return {
        "application": app_metrics,
        "health": health_score,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@root_router.get("/")
async def landing_page():
    """Landing page with service information."""
    return {
        "service": "Namaskah SMS",
        "version": "2.4.0",
        "description": "SMS Verification Service API",
        "status": "operational",
        "endpoints": {
            "health": "/system/health",
            "auth": "/auth",
            "verification": "/verify",
            "docs": "/docs",
            "redoc": "/redoc",
        },
        "message": "Welcome to Namaskah SMS API",
    }
