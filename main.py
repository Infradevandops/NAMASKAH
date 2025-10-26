"""
Namaskah SMS - Modular Application Factory
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.core.database import engine
from app.core.exceptions import setup_exception_handlers
from app.core.migration import run_startup_migrations
from app.core.caching import cache
from app.core.logging import setup_logging, get_logger
from app.models.base import Base

# Import all routers
from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.system import router as system_router, root_router
from app.api.auth import router as auth_router
from app.api.verification import router as verification_router
from app.api.wallet import router as wallet_router

# Import middleware
from app.middleware.security import (
    JWTAuthMiddleware,
    CORSMiddleware,
    SecurityHeadersMiddleware,
)
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limiting import RateLimitMiddleware


def create_app() -> FastAPI:
    """Application factory pattern"""
    # Setup logging first - before any other operations
    setup_logging()

    settings = get_settings()

    fastapi_app = FastAPI(
        title="Namaskah SMS API",
        version="2.4.0",
        description="Modular SMS Verification Service",
    )

    # Run database migrations
    # Temporarily disabled to debug startup issues
    # run_startup_migrations()

    # Setup exception handlers
    setup_exception_handlers(fastapi_app)

    # Add middleware
    fastapi_app.add_middleware(SecurityHeadersMiddleware)
    fastapi_app.add_middleware(CORSMiddleware)
    fastapi_app.add_middleware(JWTAuthMiddleware)
    fastapi_app.add_middleware(RateLimitMiddleware)
    fastapi_app.add_middleware(RequestLoggingMiddleware)

    # Include all routers
    fastapi_app.include_router(root_router)  # Root routes (landing page)
    fastapi_app.include_router(auth_router)
    fastapi_app.include_router(verification_router)
    fastapi_app.include_router(wallet_router)
    fastapi_app.include_router(admin_router)
    fastapi_app.include_router(analytics_router)
    fastapi_app.include_router(system_router)

    # Static files and templates
    fastapi_app.mount("/static", StaticFiles(directory="static"), name="static")

    # Startup and shutdown events
    @fastapi_app.on_event("startup")
    async def startup_event():
        """Initialize connections on startup."""
        await cache.connect()

    @fastapi_app.on_event("shutdown")
    async def shutdown_event():
        """Graceful cleanup on shutdown."""
        logger = get_logger("shutdown")
        logger.info("Starting graceful shutdown")

        try:
            # Disconnect cache
            await cache.disconnect()
            logger.info("Cache disconnected")

            # Dispose database connections
            engine.dispose()
            logger.info("Database connections disposed")

            logger.info("Graceful shutdown completed")
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))

    return fastapi_app


app = create_app()
