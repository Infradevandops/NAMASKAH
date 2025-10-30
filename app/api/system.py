"""System API router for health checks and service status."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.health_checks import HealthChecker, readiness_probe, liveness_probe
from app.core.monitoring import dashboard_metrics
from app.schemas import ServiceStatusSummary, ServiceStatus

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
    return JSONResponse(
        status_code=status_code,
        content={"ready": is_ready}
    )


@router.get("/health/liveness")
async def liveness_check():
    """Kubernetes liveness probe."""
    from fastapi.responses import JSONResponse
    is_alive = await liveness_probe()
    status_code = 200 if is_alive else 503
    return JSONResponse(
        status_code=status_code,
        content={"alive": is_alive}
    )


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
            last_checked=service.last_checked
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
            "down": status_counts.get("down", 0)
        }
    
    return ServiceStatusSummary(
        overall_status=overall_status,
        services=service_statuses,
        stats=stats,
        last_updated=datetime.now(timezone.utc)
    )


@router.get("/info")
def get_system_info():
    """Get basic system information."""
    return {
        "service_name": "Namaskah SMS",
        "version": "2.3.0",
        "environment": getattr(settings, 'environment', 'production'),
        "features": {
            "sms_verification": True,
            "payment_processing": True,
            "admin_panel": True,
            "analytics": True
        },
        "limits": {
            "max_concurrent_verifications": 100,
            "rate_limit_per_minute": 60,
            "max_api_keys_per_user": 5
        }
    }


@router.get("/config")
def get_public_config():
    """Get public configuration settings."""
    return {
        "supported_services": [
            "telegram", "whatsapp", "discord", "instagram", 
            "twitter", "facebook", "google", "microsoft"
        ],
        "payment_methods": ["paystack"],
        "currencies": ["NGN"],
        "min_credit_amount": 100.0,
        "verification_timeout_minutes": 10,
        "api_version": "v1"
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
    from app.core.metrics import get_prometheus_metrics as get_prom_metrics, get_metrics_content_type
    from fastapi.responses import Response
    
    metrics_data = get_prom_metrics()
    return Response(
        content=metrics_data,
        media_type=get_metrics_content_type()
    )


@router.get("/metrics/application")
async def get_application_metrics():
    """Get application-specific metrics."""
    from app.core.metrics import metrics_collector
    
    app_metrics = metrics_collector.get_application_metrics()
    health_score = metrics_collector.get_health_score()
    
    return {
        "application": app_metrics,
        "health": health_score,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@root_router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page with service information."""
    try:
        # Initialize templates
        templates = Jinja2Templates(directory="templates")
        
        # Context data for the template
        context = {
            "request": request,
            "service_name": "Namaskah SMS",
            "version": "2.4.0",
            "description": "SMS Verification Service API",
            "status": "operational",
            "total_services": 1807,
            "success_rate": 95,
            "active_users": 5247,
            "verifications_today": 15234
        }
        
        # Render the landing page template
        return templates.TemplateResponse("landing.html", context)
        
    except Exception as e:
        # Fallback to JSON response if template fails
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Landing page template error: %s", str(e), exc_info=True)
        
        # Return simple HTML as fallback
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Namaskah SMS</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 40px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #667eea; margin-bottom: 20px; }}
                .status {{ color: #10b981; font-weight: bold; }}
                .endpoints {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .endpoints a {{ color: #667eea; text-decoration: none; display: block; margin: 5px 0; }}
                .endpoints a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Namaskah SMS</h1>
                <p><strong>Version:</strong> 2.4.0</p>
                <p><strong>Description:</strong> SMS Verification Service API</p>
                <p><strong>Status:</strong> <span class="status">Operational</span></p>
                
                <div class="endpoints">
                    <h3>Available Endpoints:</h3>
                    <a href="/app">📱 Main Dashboard</a>
                    <a href="/system/health">🏥 Health Check</a>
                    <a href="/auth">🔐 Authentication</a>
                    <a href="/verify">📱 SMS Verification</a>
                    <a href="/docs">📚 API Documentation</a>
                    <a href="/redoc">📖 ReDoc Documentation</a>
                </div>
                
                <p><em>Welcome to Namaskah SMS API - Your reliable SMS verification service!</em></p>
            </div>
        </body>
        </html>
        """, status_code=200)


@root_router.get("/app", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Main dashboard/application page."""
    try:
        # Initialize templates
        templates = Jinja2Templates(directory="templates")
        
        # Context data for the dashboard
        context = {
            "request": request,
            "service_name": "Namaskah SMS",
            "version": "2.4.0",
            "user": {
                "name": "User",
                "credits": 0,
                "free_verifications": 1
            },
            "stats": {
                "total_services": 1807,
                "success_rate": 95,
                "active_users": 5247,
                "verifications_today": 15234
            }
        }
        
        # Try to render the dashboard template
        return templates.TemplateResponse("dashboard.html", context)
        
    except Exception as e:
        # Fallback to simple dashboard HTML
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Dashboard template error: %s", str(e), exc_info=True)
        
        # Return simple dashboard as fallback
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Namaskah SMS - Dashboard</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f5f7fa; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; }
                .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 20px 0; }
                .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
                .stat-card { background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
                .stat-number { font-size: 2rem; font-weight: bold; color: #667eea; }
                .cta-button { background: #667eea; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; text-decoration: none; display: inline-block; }
                .cta-button:hover { background: #5a67d8; }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="container">
                    <h1>📱 Namaskah SMS Dashboard</h1>
                    <p>SMS Verification Service - Get started with 1 free verification!</p>
                </div>
            </div>
            
            <div class="container">
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number">1,807</div>
                        <div>Supported Services</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">95%</div>
                        <div>Success Rate</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">5,247</div>
                        <div>Active Users</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">15,234</div>
                        <div>Verifications Today</div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🚀 Get Started</h2>
                    <p>Welcome to Namaskah SMS! You have <strong>1 free verification</strong> to get started.</p>
                    <p>Verify accounts for WhatsApp, Telegram, Google, Discord, Instagram, and 1,800+ more services.</p>
                    
                    <div style="margin: 20px 0;">
                        <a href="/auth/register" class="cta-button">Create Account</a>
                        <a href="/auth/login" class="cta-button" style="background: #10b981;">Login</a>
                        <a href="/docs" class="cta-button" style="background: #6b7280;">API Docs</a>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📋 Quick Actions</h3>
                    <ul>
                        <li><a href="/verify/create">🆕 Create New Verification</a></li>
                        <li><a href="/wallet/balance">💰 Check Balance</a></li>
                        <li><a href="/auth/api-keys">🔑 Manage API Keys</a></li>
                        <li><a href="/system/health">🏥 System Status</a></li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """, status_code=200)


@root_router.get("/services", response_class=HTMLResponse)
async def services_page(request: Request):
    """Services listing page."""
    try:
        templates = Jinja2Templates(directory="templates")
        context = {
            "request": request,
            "service_name": "Namaskah SMS",
            "total_services": 1807
        }
        return templates.TemplateResponse("services.html", context)
    except Exception:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>Services - Namaskah SMS</title></head>
        <body>
            <h1>📱 Supported Services</h1>
            <p>We support 1,807+ services including:</p>
            <ul>
                <li>WhatsApp</li>
                <li>Telegram</li>
                <li>Google</li>
                <li>Discord</li>
                <li>Instagram</li>
                <li>And 1,800+ more...</li>
            </ul>
            <a href="/app">← Back to Dashboard</a>
        </body>
        </html>
        """)


@root_router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """Pricing page."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pricing - Namaskah SMS</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; }
            .price { font-size: 3rem; color: #667eea; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💰 Simple Pricing</h1>
            <div class="price">₦1</div>
            <p>Per SMS verification</p>
            <ul>
                <li>✅ 1 Free verification on signup</li>
                <li>✅ Pay as you go - no subscriptions</li>
                <li>✅ Auto-refund if SMS not received</li>
                <li>✅ 95%+ success rate</li>
                <li>✅ 1,807+ supported services</li>
            </ul>
            <a href="/app" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Get Started</a>
        </div>
    </body>
    </html>
    """)


@root_router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """About page."""
    try:
        templates = Jinja2Templates(directory="templates")
        context = {"request": request, "service_name": "Namaskah SMS"}
        return templates.TemplateResponse("about.html", context)
    except Exception:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>About - Namaskah SMS</title></head>
        <body>
            <h1>About Namaskah SMS</h1>
            <p>Reliable SMS verification service for 1,807+ platforms.</p>
            <p>Fast, secure, and affordable SMS verification solutions.</p>
            <a href="/">← Back to Home</a>
        </body>
        </html>
        """)


@root_router.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    """Contact page."""
    try:
        templates = Jinja2Templates(directory="templates")
        context = {"request": request, "service_name": "Namaskah SMS"}
        return templates.TemplateResponse("contact.html", context)
    except Exception:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>Contact - Namaskah SMS</title></head>
        <body>
            <h1>Contact Us</h1>
            <p>Need help? We're here for you!</p>
            <ul>
                <li>📧 Email: support@namaskah.app</li>
                <li>💬 Live Chat: Available 24/7</li>
                <li>📚 Documentation: <a href="/docs">/docs</a></li>
            </ul>
            <a href="/">← Back to Home</a>
        </body>
        </html>
        """)


@root_router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Admin dashboard page."""
    try:
        templates = Jinja2Templates(directory="templates")
        context = {
            "request": request,
            "service_name": "Namaskah SMS",
            "version": "2.4.0"
        }
        return templates.TemplateResponse("admin.html", context)
    except Exception:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Dashboard - Namaskah SMS</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f5f7fa; }
                .header { background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; padding: 20px; }
                .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 20px 0; }
                .admin-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
                .admin-card { background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid #dc2626; }
                .admin-number { font-size: 2rem; font-weight: bold; color: #dc2626; }
                .cta-button { background: #dc2626; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; text-decoration: none; display: inline-block; margin: 5px; }
                .cta-button:hover { background: #b91c1c; }
                .warning { background: #fef3c7; border: 1px solid #f59e0b; padding: 15px; border-radius: 8px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="container">
                    <h1>🛡️ Admin Dashboard</h1>
                    <p>Namaskah SMS Administration Panel</p>
                </div>
            </div>
            
            <div class="container">
                <div class="warning">
                    <h3>⚠️ Authentication Required</h3>
                    <p>This is the admin dashboard. Please log in with admin credentials to access admin features.</p>
                </div>
                
                <div class="card">
                    <h2>🔐 Admin Access</h2>
                    <p>To access admin features, you need to:</p>
                    <ol>
                        <li>Log in with an admin account</li>
                        <li>Have admin privileges enabled</li>
                        <li>Use proper authentication headers for API access</li>
                    </ol>
                    
                    <div style="margin: 20px 0;">
                        <a href="/auth/login" class="cta-button">Admin Login</a>
                        <a href="/docs" class="cta-button" style="background: #6b7280;">API Docs</a>
                        <a href="/" class="cta-button" style="background: #10b981;">← Back Home</a>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📋 Admin API Endpoints</h3>
                    <p>Available admin endpoints (require authentication):</p>
                    <ul>
                        <li><code>GET /admin/users</code> - List all users</li>
                        <li><code>GET /admin/stats</code> - System statistics</li>
                        <li><code>GET /admin/support/tickets</code> - Support tickets</li>
                        <li><code>PUT /admin/users/{user_id}</code> - Update user</li>
                        <li><code>DELETE /admin/users/{user_id}</code> - Delete user</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """)