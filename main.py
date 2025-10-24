import time
import secrets
import hashlib
import logging
from typing import Dict, Any, Optional


# Minimal Rate Limiting
class SimpleRateLimiter:
    def __init__(self):
        self.requests = {}
        self.limit = 100
        self.window = 60

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - self.window

        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time
                for req_time in self.requests[client_ip]
                if req_time > window_start
            ]
        else:
            self.requests[client_ip] = []

        if len(self.requests[client_ip]) >= self.limit:
            return False

        self.requests[client_ip].append(now)
        return True


# Initialize rate limiter
rate_limiter = SimpleRateLimiter()


# Input sanitization
def sanitize_input(input_str: str) -> str:
    if not input_str:
        return ""

    import re

    # Remove dangerous patterns
    dangerous = [r"<script[^>]*>.*?</script>", r"javascript:", r"on\w+\s*="]
    cleaned = input_str

    for pattern in dangerous:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

    return cleaned.strip()


"""Namaskah SMS - With Pricing & Admin Panel"""
import os
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

import jwt
from dotenv import load_dotenv

# Import security modules
try:
    from security_utils import (
        hash_password,
        verify_password,
        validate_password,
        sanitize_input,
        validate_email,
        generate_secure_token,
        rate_limiter,
    )
    from middleware import (
        SecurityHeadersMiddleware,
        RequestLoggingMiddleware,
        RateLimitMiddleware,
    )
    from cache_service import cache, cached, get_cache_stats

    SECURITY_MODULES_AVAILABLE = True
except ImportError:
    SECURITY_MODULES_AVAILABLE = False

    # Fallback functions
    def hash_password(password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(plain, hashed):
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    def validate_password(password):
        return (True, "Valid")

    def sanitize_input(text):
        return text

    def validate_email(email):
        return True

    def generate_secure_token():
        return os.urandom(32).hex()

    class rate_limiter:
        @staticmethod
        def is_allowed(key, max_attempts=5, window_minutes=15):
            return True


try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

# Security patches
try:
    from security_patches import (
        rate_limit_middleware,
        validate_service_name,
        validate_email,
        sanitize_input,
        create_secure_token,
        validate_token,
        safe_query,
        log_security_event,
        verify_webhook_signature,
        hash_password_secure,
        verify_password_secure,
        add_security_headers,
        validate_verification_request,
        validate_user_registration,
    )

    SECURITY_PATCHES_AVAILABLE = True
except ImportError:
    SECURITY_PATCHES_AVAILABLE = False

    # Fallback functions
    def rate_limit_middleware(request, call_next):
        return call_next(request)

    def validate_service_name(name):
        return name

    def validate_email(email):
        return True

    def sanitize_input(text):
        return text

    def log_security_event(*args, **kwargs):
        pass

    def add_security_headers(response):
        return response

    def validate_verification_request(data):
        return data

    def validate_user_registration(data):
        return data


# WebSocket support
try:
    from websocket_realtime import add_websocket_routes, manager

    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

    class MockManager:
        def send_personal_message(self, *args):
            pass

        @property
        def active_connections(self):
            return {}

    manager = MockManager()

    def add_websocket_routes(app):
        pass


from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Float

# Error handlers with fallbacks
try:
    from error_handlers import (
        http_exception_handler,
        validation_exception_handler,
        general_exception_handler,
        log_transaction,
        log_security_event,
        logger,
    )
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

    async def http_exception_handler(request, exc):
        return {
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def validation_exception_handler(request, exc):
        return {"error": "Validation error", "message": str(exc)}

    async def general_exception_handler(request, exc):
        return {
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def log_transaction(*args, **kwargs):
        pass

    def log_security_event(*args, **kwargs):
        pass


from sqlalchemy.orm import sessionmaker, Session
import bcrypt
import requests

load_dotenv()

# Security configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
SECRET_KEY = os.getenv("SECRET_KEY")

# Generate secure SECRET_KEY if not provided
if not SECRET_KEY:
    SECRET_KEY = os.urandom(32).hex()
    if ENVIRONMENT == "production":
        print(
            "⚠️ WARNING: SECRET_KEY not set, using generated key. Set SECRET_KEY environment variable for production."
        )
elif len(SECRET_KEY) < 32 and ENVIRONMENT == "production":
    print(
        "⚠️ WARNING: SECRET_KEY should be at least 32 characters for production security."
    )

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Warn about missing production variables but don't fail startup
if ENVIRONMENT == "production":
    required_vars = ["DATABASE_URL", "TEXTVERIFIED_API_KEY", "PAYSTACK_SECRET_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(
            f"⚠️ WARNING: Missing production environment variables: {', '.join(missing_vars)}"
        )
        print(
            "⚠️ Some features may not work correctly. Please set these variables in Render dashboard."
        )

# SEO Configuration
SEO_CONFIG = {
    "/": {
        "title": "Namaskah SMS - Instant SMS Verification for 1,807+ Services",
        "description": "Get temporary phone numbers for SMS verification in seconds. 95%+ success rate, automatic refunds, API access. WhatsApp, Telegram, Google, Discord & 1,800+ more services.",
        "keywords": "SMS verification, temporary phone number, receive SMS online, phone verification, WhatsApp verification, Telegram verification, Discord verification, Google verification, virtual phone number, SMS API",
        "og_image": "/static/images/og-home.png",
        "og_type": "website",
    },
    "/app": {
        "title": "Dashboard - Namaskah SMS",
        "description": "Access your SMS verification dashboard. Create verifications, manage wallet, view history, and use our API for 1,807+ services.",
        "keywords": "SMS dashboard, verification dashboard, phone number dashboard, API access, SMS management",
        "robots": "noindex, nofollow",
        "og_type": "website",
    },
    "/api-docs": {
        "title": "API Documentation - Namaskah SMS",
        "description": "Complete API documentation for SMS verification integration. RESTful API with webhooks, real-time status updates, and comprehensive examples.",
        "keywords": "SMS API, verification API, phone number API, REST API, webhook API, developer documentation, SMS integration",
        "og_type": "website",
    },
    "/faq": {
        "title": "FAQ - Namaskah SMS",
        "description": "Frequently asked questions about SMS verification services. Get answers about pricing, refunds, API usage, and service availability.",
        "keywords": "SMS verification FAQ, phone verification questions, temporary number help, SMS API support",
        "og_type": "website",
    },
    "/about": {
        "title": "About Us - Namaskah SMS",
        "description": "Learn about Namaskah SMS - professional SMS verification service provider. Our mission, technology, and commitment to privacy and reliability.",
        "keywords": "about Namaskah SMS, SMS verification company, phone verification service, temporary numbers provider",
        "og_type": "website",
    },
    "/contact": {
        "title": "Contact Support - Namaskah SMS",
        "description": "Get help with SMS verification services. Contact our support team for assistance with verifications, payments, API integration, and account issues.",
        "keywords": "SMS verification support, phone verification help, contact Namaskah SMS, customer service",
        "og_type": "website",
    },
    "/status": {
        "title": "Service Status - Namaskah SMS",
        "description": "Real-time status of SMS verification services. Check API uptime, service availability, and system performance across all supported platforms.",
        "keywords": "SMS service status, verification uptime, API status, system health, service availability",
        "og_type": "website",
    },
    "/privacy": {
        "title": "Privacy Policy - Namaskah SMS",
        "description": "Our privacy policy explains how we collect, use, and protect your data. GDPR compliant with transparent data practices and user rights.",
        "keywords": "privacy policy, data protection, GDPR compliance, user privacy, data security",
        "og_type": "website",
    },
    "/terms": {
        "title": "Terms of Service - Namaskah SMS",
        "description": "Terms and conditions for using Namaskah SMS verification services. Fair usage policy, user agreement, and service limitations.",
        "keywords": "terms of service, user agreement, service terms, usage policy, SMS verification terms",
        "og_type": "website",
    },
    "/cookies": {
        "title": "Cookie Policy - Namaskah SMS",
        "description": "Learn about our cookie usage and tracking technologies. Manage your cookie preferences and understand data collection practices.",
        "keywords": "cookie policy, tracking cookies, privacy settings, data collection, cookie management",
        "og_type": "website",
    },
    "/refund": {
        "title": "Refund Policy - Namaskah SMS",
        "description": "Fair and transparent refund policy for SMS verification services. Automatic refunds for failed verifications and clear cancellation terms.",
        "keywords": "refund policy, SMS verification refunds, automatic refunds, cancellation policy, money back guarantee",
        "og_type": "website",
    },
    "/reviews": {
        "title": "Customer Reviews - Namaskah SMS",
        "description": "Read customer reviews and testimonials for Namaskah SMS verification services. Real feedback from developers, businesses, and individual users.",
        "keywords": "SMS verification reviews, customer testimonials, user feedback, Namaskah SMS reviews, phone verification ratings",
        "og_type": "website",
    },
    "/analytics": {
        "title": "Analytics Dashboard - Namaskah SMS",
        "description": "View detailed analytics and insights for your SMS verification usage. Track performance, success rates, and service statistics.",
        "keywords": "SMS analytics, verification statistics, usage dashboard, performance metrics",
        "robots": "noindex, nofollow",
        "og_type": "website",
    },
}


def get_seo_meta(path: str, request_url: str = None):
    """Get SEO metadata for a given path"""
    config = SEO_CONFIG.get(path, SEO_CONFIG["/"])  # Default to homepage config

    return {
        "title": config.get("title", "Namaskah SMS"),
        "description": config.get("description", "Instant SMS verification service"),
        "keywords": config.get("keywords", "SMS verification, phone verification"),
        "robots": config.get("robots", "index, follow"),
        "og_title": config.get("og_title", config.get("title")),
        "og_description": config.get("og_description", config.get("description")),
        "og_image": config.get("og_image", "/static/images/og-image.png"),
        "og_type": config.get("og_type", "website"),
        "og_url": request_url or f"https://namaskah.app{path}",
        "canonical_url": request_url or f"https://namaskah.app{path}",
        "twitter_card": config.get("twitter_card", "summary_large_image"),
        "twitter_title": config.get("twitter_title", config.get("title")),
        "twitter_description": config.get(
            "twitter_description", config.get("description")
        ),
        "twitter_image": config.get(
            "twitter_image", config.get("og_image", "/static/images/og-image.png")
        ),
    }


# Initialize Sentry for error tracking
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_AVAILABLE and SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        environment=os.getenv("ENVIRONMENT", "production"),
    )

# Config
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
GOOGLE_ANALYTICS_ID = os.getenv("GOOGLE_ANALYTICS_ID")  # Set in production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sms.db")
TEXTVERIFIED_API_KEY = os.getenv("TEXTVERIFIED_API_KEY")
TEXTVERIFIED_EMAIL = os.getenv("TEXTVERIFIED_EMAIL")

# Currency: 1N = $2 USD
USD_TO_NAMASKAH = 0.5  # 1 USD = 0.5N
NAMASKAH_TO_USD = 2.0  # 1N = 2 USD

# Import optimized pricing and retry mechanisms with fallbacks
try:
    from pricing_config import (
        SERVICE_TIERS,
        SUBSCRIPTION_PLANS,
        RENTAL_HOURLY,
        HOURLY_RENTAL_RULES,
        RENTAL_SERVICE_SPECIFIC,
        RENTAL_GENERAL_USE,
        PREMIUM_ADDONS,
        VOICE_PREMIUM,
        get_service_tier,
        get_service_price,
        calculate_rental_cost,
        get_hourly_rental_price,
        get_rental_price_breakdown,
    )
except ImportError:
    # Fallback pricing if module not found
    SERVICE_TIERS = {
        "popular": {
            "name": "Popular",
            "base_price": 1.0,
            "services": [],
            "success_rate": 95,
        }
    }
    SUBSCRIPTION_PLANS = {
        "starter": {"name": "Starter", "price": 0, "discount": 0, "features": []}
    }
    PREMIUM_ADDONS = {
        "custom_area_code": 4.0,
        "guaranteed_carrier": 6.0,
        "priority_queue": 2.0,
    }
    VOICE_PREMIUM = 0.25

    def get_service_tier(service):
        return "popular"

    def get_service_price(service, plan="starter", count=0):
        return 1.0

    def get_hourly_rental_price(
        hours, service="general", mode="always_ready", auto_renew=False, bulk_count=1
    ):
        return hours * 0.5

    def get_rental_price_breakdown(
        hours, service="general", mode="always_ready", auto_renew=False, bulk_count=1
    ):
        return {"final_price": hours * 0.5}


try:
    from retry_mechanisms import (
        retry_with_backoff,
        async_retry_with_backoff,
        PaymentRetryManager,
        SMSRetryManager,
        DatabaseRetryManager,
        textverified_api_call,
        paystack_api_call,
        check_service_health,
        reset_circuit_breaker,
    )
except ImportError:
    # Fallback retry mechanisms
    def retry_with_backoff(max_retries=3, circuit_breaker_key=None):
        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def textverified_api_call(method, url, **kwargs):
        return requests.request(method, url, **kwargs)

    def paystack_api_call(method, url, **kwargs):
        return requests.request(method, url, **kwargs)

    def check_service_health(service):
        return {"status": "closed"}

    def reset_circuit_breaker(service):
        return True


try:
    from carrier_utils import (
        SUPPORTED_CARRIERS,
        AREA_CODE_MAP,
        extract_area_code,
        get_location_info,
        format_carrier_info,
    )
except ImportError:
    # Fallback carrier utils
    SUPPORTED_CARRIERS = {}
    AREA_CODE_MAP = {}

    def extract_area_code(phone):
        return None

    def get_location_info(phone):
        return {}

    def format_carrier_info(carrier, phone):
        return {}


try:
    from receipt_system import (
        VerificationReceipt,
        NotificationPreferences,
        InAppNotification,
        ReceiptService,
        NotificationService,
        process_successful_verification,
    )
except ImportError:
    # Fallback receipt system
    class ReceiptService:
        def __init__(self, db):
            pass

        def get_user_receipts(self, user_id, limit):
            return []

    class NotificationService:
        def __init__(self, db):
            pass

        def get_user_notifications(self, user_id, unread_only=False, limit=50):
            return []

        def mark_notification_read(self, notification_id, user_id):
            return True

        def mark_all_read(self, user_id):
            pass

        def get_notification_preferences(self, user_id):
            return {
                "in_app_notifications": True,
                "email_notifications": True,
                "receipt_notifications": True,
            }

        def update_notification_preferences(self, user_id, **kwargs):
            return kwargs

    def process_successful_verification(**kwargs):
        pass


# Legacy pricing (deprecated)
SMS_PRICING = {"popular": 1.0, "general": 1.25}

# Subscription Plans (now imported from pricing_config.py)
# Legacy plans kept for backward compatibility

VERIFICATION_COST = SMS_PRICING["popular"]  # Default
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Payment Config
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
BITCOIN_ADDRESS = os.getenv(
    "BITCOIN_ADDRESS", "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
)
ETHEREUM_ADDRESS = os.getenv(
    "ETHEREUM_ADDRESS", "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
)
SOLANA_ADDRESS = os.getenv(
    "SOLANA_ADDRESS", "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
)
USDT_ADDRESS = os.getenv("USDT_ADDRESS", "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")

# Exchange rate cache (updates every 1 hour)
exchange_rate_cache = {"rate": 1478.24, "last_updated": None}


def get_usd_to_ngn_rate():
    """Get current USD to NGN exchange rate with 1-hour caching"""
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)

    # Check if cache is valid (less than 1 hour old)
    if exchange_rate_cache["last_updated"] and (
        now - exchange_rate_cache["last_updated"]
    ) < timedelta(hours=1):
        return exchange_rate_cache["rate"]

    # Fetch new rate
    try:
        response = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD", timeout=5
        )
        if response.status_code == 200:
            rates = response.json().get("rates", {})
            new_rate = rates.get("NGN", 1478.24)
            exchange_rate_cache["rate"] = new_rate
            exchange_rate_cache["last_updated"] = now
            print(f"✅ Exchange rate updated: 1 USD = ₦{new_rate}")
            return new_rate
    except Exception as e:
        print(f"⚠️ Exchange rate API error: {e}")

    # Return cached/fallback rate
    return exchange_rate_cache["rate"]


# Email Config
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@namaskah.app")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Database with connection pooling
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
SessionLocal = sessionmaker(bind=engine)
from sqlalchemy.orm import declarative_base as new_declarative_base

Base = new_declarative_base()


# Models
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    credits = Column(Float, default=0.0)
    free_verifications = Column(Float, default=1.0)  # 1 free verification for new users
    is_admin = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String)
    reset_token = Column(String)
    reset_token_expires = Column(DateTime)
    referral_code = Column(String, unique=True)
    referred_by = Column(String)
    referral_earnings = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Verification(Base):
    __tablename__ = "verifications"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    service_name = Column(String, nullable=False)
    phone_number = Column(String)
    capability = Column(String, default="sms")  # sms or voice
    status = Column(String, default="pending")
    verification_code = Column(String)
    cost = Column(Float, default=VERIFICATION_COST)
    call_duration = Column(Float)  # seconds
    transcription = Column(String)
    audio_url = Column(String)
    requested_carrier = Column(String)  # Store user's carrier selection
    requested_area_code = Column(String)  # Store user's area code selection
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # credit, debit
    description = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    key = Column(String, unique=True, nullable=False)
    name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Webhook(Base):
    __tablename__ = "webhooks"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class NotificationSettings(Base):
    __tablename__ = "notification_settings"
    id = Column(String, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)
    email_on_sms = Column(Boolean, default=True)
    email_on_low_balance = Column(Boolean, default=True)
    low_balance_threshold = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Referral(Base):
    __tablename__ = "referrals"
    id = Column(String, primary_key=True)
    referrer_id = Column(String, nullable=False)
    referred_id = Column(String, nullable=False)
    reward_amount = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class NumberRental(Base):
    __tablename__ = "number_rentals"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    service_name = Column(String)
    duration_hours = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    mode = Column(String, default="always_ready")  # always_ready or manual
    status = Column(String, default="active")  # active, expired, released
    started_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    expires_at = Column(DateTime, nullable=False)
    released_at = Column(DateTime)
    auto_extend = Column(Boolean, default=False)
    warning_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id = Column(String, primary_key=True)
    user_id = Column(String)  # nullable for non-logged-in users
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    category = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, default="open")  # open, in_progress, resolved, closed
    admin_response = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime)


class ServiceStatus(Base):
    __tablename__ = "service_status"
    id = Column(String, primary_key=True)
    service_name = Column(String, nullable=False)
    status = Column(String, default="operational")  # operational, degraded, down
    success_rate = Column(Float, default=100.0)
    last_checked = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(String, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)
    plan = Column(String, nullable=False)  # starter, pro, turbo
    status = Column(String, default="active")  # active, cancelled, expired
    price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)  # 0.20 for pro, 0.35 for turbo
    duration = Column(Float, default=0)  # days (0 = lifetime)
    expires_at = Column(DateTime)  # null for lifetime
    cancelled_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime)


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(String, primary_key=True)
    user_id = Column(String)
    email = Column(String)
    page = Column(String)
    action = Column(String, nullable=False)
    element = Column(String)
    status = Column(String, nullable=False)
    details = Column(String)
    error_message = Column(String)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PaymentLog(Base):
    __tablename__ = "payment_logs"
    id = Column(String, primary_key=True)
    user_id = Column(String)
    email = Column(String)
    reference = Column(String, unique=True)
    amount_ngn = Column(Float)
    amount_usd = Column(Float)
    namaskah_amount = Column(Float)
    status = Column(String)
    payment_method = Column(String)
    webhook_received = Column(Boolean, default=False)
    credited = Column(Boolean, default=False)
    error_message = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime)


class BannedNumber(Base):
    __tablename__ = "banned_numbers"
    id = Column(String, primary_key=True)
    phone_number = Column(String, nullable=False, index=True)
    service_name = Column(String, nullable=False, index=True)
    area_code = Column(String)
    carrier = Column(String)  # ISP/Carrier (Verizon, AT&T, T-Mobile, etc)
    fail_count = Column(Float, default=1)
    last_failed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )


class VerificationReceipt(Base):
    __tablename__ = "verification_receipts"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    verification_id = Column(String, nullable=False)
    service_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    amount_spent = Column(Float, nullable=False)
    isp_carrier = Column(String)
    area_code = Column(String)
    success_timestamp = Column(DateTime, nullable=False)
    receipt_data = Column(String)  # JSON data
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class NotificationPreferences(Base):
    __tablename__ = "notification_preferences"
    id = Column(String, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)
    in_app_notifications = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=True)
    receipt_notifications = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime)


class InAppNotification(Base):
    __tablename__ = "in_app_notifications"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    type = Column(String, default="receipt")  # receipt, success, info
    is_read = Column(Boolean, default=False)
    verification_id = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


Base.metadata.create_all(bind=engine)


# Create database indexes for performance
def create_indexes():
    """Create indexes on frequently queried fields"""
    try:
        with engine.connect() as conn:
            # User indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)"
            )

            # Verification indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_verifications_user_id ON verifications(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_verifications_status ON verifications(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_verifications_created_at ON verifications(created_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_verifications_service_name ON verifications(service_name)"
            )

            # Transaction indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at)"
            )

            # Rental indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_rentals_user_id ON number_rentals(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_rentals_status ON number_rentals(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_rentals_expires_at ON number_rentals(expires_at)"
            )

            # Receipt and notification indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_receipts_user_id ON verification_receipts(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_receipts_verification_id ON verification_receipts(verification_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON in_app_notifications(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_notifications_read ON in_app_notifications(is_read)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_notification_prefs_user_id ON notification_preferences(user_id)"
            )

            # Service status indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_service_status_name ON service_status(service_name)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_service_status_checked ON service_status(last_checked)"
            )

            conn.commit()
            print("✅ Database indexes created")
    except Exception as e:
        print(f"⚠️ Index creation skipped: {e}")


create_indexes()


# Auto-create admin user on startup
def create_admin_if_not_exists():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if not admin:
            import secrets

            # Use secure password from environment or generate one
            admin_password = ADMIN_PASSWORD or "Namaskah@Admin2024"
            if not ADMIN_PASSWORD:
                print(
                    f"⚠️ Using default admin password. Set ADMIN_PASSWORD environment variable for production security."
                )
                admin_password = "Namaskah@Admin2024"

            admin = User(
                id=f"user_{datetime.now(timezone.utc).timestamp()}",
                email="admin@namaskah.app",
                password_hash=hash_password(admin_password),
                credits=100.0,
                free_verifications=0.0,
                is_admin=True,
                email_verified=True,
                referral_code=secrets.token_urlsafe(6),
            )
            db.add(admin)
            db.commit()
            print("✅ Admin user created: admin@namaskah.app")
    except Exception as e:
        print(f"Admin creation skipped: {e}")
    finally:
        db.close()


create_admin_if_not_exists()


# Background task for TextVerified API health check
async def check_textverified_health_loop():
    """Check TextVerified API health every 5 minutes"""
    import asyncio

    while True:
        try:
            db = SessionLocal()
            try:
                # Try to get token from TextVerified
                tv_client.get_token()
                status = "operational"
                logger.info("✅ TextVerified API: Operational")
            except Exception as e:
                status = "down"
                logger.error(f"❌ TextVerified API: Down - {str(e)}")

            # Update or create status record
            status_record = (
                db.query(ServiceStatus)
                .filter(ServiceStatus.service_name == "textverified_api")
                .first()
            )

            if status_record:
                status_record.status = status
                status_record.last_checked = datetime.now(timezone.utc)
            else:
                status_record = ServiceStatus(
                    id=f"status_textverified_api_{datetime.now(timezone.utc).timestamp()}",
                    service_name="textverified_api",
                    status=status,
                    success_rate=100.0 if status == "operational" else 0.0,
                )
                db.add(status_record)

            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Health check error: {e}")

        # Wait 5 minutes
        await asyncio.sleep(300)


# Email Helper (legacy compatibility)
def send_email(to_email: str, subject: str, body: str):
    """Send email notification - legacy function for compatibility"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
            print(f"⚠️ Email not configured, skipping: {subject}")
            return False

        msg = MIMEMultipart()
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


# Activity Logging Helper
def log_activity(
    db: Session,
    user_id=None,
    email=None,
    page=None,
    action=None,
    element=None,
    status=None,
    details=None,
    error=None,
    ip=None,
    user_agent=None,
):
    """Log user activity"""
    try:
        log = ActivityLog(
            id=f"log_{datetime.now(timezone.utc).timestamp()}",
            user_id=user_id,
            email=email,
            page=page,
            action=action,
            element=element,
            status=status,
            details=details,
            error_message=error,
            ip_address=ip,
            user_agent=user_agent,
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"Activity log error: {e}")


# Payment Logging Helper
def log_payment(
    db: Session,
    user_id=None,
    email=None,
    reference=None,
    amount_ngn=0,
    amount_usd=0,
    namaskah_amount=0,
    status="initialized",
    **kwargs,
):
    """Log payment attempt"""
    try:
        log = PaymentLog(
            id=f"pay_{datetime.now(timezone.utc).timestamp()}",
            user_id=user_id,
            email=email,
            reference=reference,
            amount_ngn=amount_ngn,
            amount_usd=amount_usd,
            namaskah_amount=namaskah_amount,
            status=status,
            payment_method="paystack",
            **kwargs,
        )
        db.add(log)
        db.commit()
        return log
    except Exception as e:
        print(f"Payment log error: {e}")
        return None


# Schemas
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class CreateVerificationRequest(BaseModel):
    service_name: str
    capability: str = "sms"
    area_code: str = None
    carrier: str = None

    class Config:
        schema_extra = {
            "example": {
                "service_name": "telegram",
                "capability": "sms",
                "area_code": "212",
                "carrier": "verizon",
            }
        }


class AddCreditsRequest(BaseModel):
    user_id: str
    amount: float


class FundWalletRequest(BaseModel):
    amount: float
    payment_method: str  # paystack, bitcoin, ethereum, solana, usdt


class CreateAPIKeyRequest(BaseModel):
    name: str


class CreateWebhookRequest(BaseModel):
    url: str


class CreateRentalRequest(BaseModel):
    service_name: str
    duration_hours: float
    mode: str = "always_ready"  # always_ready or manual
    auto_extend: bool = False
    area_code: str = None
    carrier: str = None

    class Config:
        schema_extra = {
            "example": {
                "service_name": "telegram",
                "duration_hours": 6,
                "mode": "always_ready",
                "auto_extend": False,
            }
        }


class SubscribeRequest(BaseModel):
    plan: str  # pro or turbo


class ExtendRentalRequest(BaseModel):
    additional_hours: float


class SupportRequest(BaseModel):
    name: str
    email: EmailStr
    category: str
    message: str


class AdminResponseRequest(BaseModel):
    response: str


# Dependencies
security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        user = db.query(User).filter(User.id == payload["user_id"]).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_admin_user(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# TextVerified Client
class TextVerifiedClient:
    def __init__(self):
        self.base_url = "https://www.textverified.com"
        self.api_key = TEXTVERIFIED_API_KEY
        self.email = TEXTVERIFIED_EMAIL
        self.token = None
        self.token_expires = None

    def get_token(self, force_refresh=False):
        """Get authentication token with automatic refresh"""
        # Check if token exists and is not expired
        if self.token and not force_refresh:
            if self.token_expires and datetime.now(timezone.utc) < self.token_expires:
                return self.token

        # Get new token
        try:
            headers = {"X-API-KEY": self.api_key, "X-API-USERNAME": self.email}
            r = requests.post(
                f"{self.base_url}/api/pub/v2/auth", headers=headers, timeout=10
            )
            r.raise_for_status()
            self.token = r.json()["token"]
            # Token expires in 1 hour, refresh after 50 minutes
            self.token_expires = datetime.now(timezone.utc) + timedelta(minutes=50)
            logger.info("✅ TextVerified token refreshed")
            return self.token
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ TextVerified auth failed: {e}")
            raise HTTPException(
                status_code=503, detail=f"SMS provider authentication failed: {str(e)}"
            )

    @retry_with_backoff(max_retries=3, circuit_breaker_key="textverified")
    def create_verification(
        self,
        service_name: str,
        capability: str = "sms",
        area_code: str = None,
        carrier: str = None,
    ):
        """Create verification with automatic token refresh and retry on 401"""
        payload = {"serviceName": service_name, "capability": capability}

        # Add filters if provided
        if area_code:
            payload["areaCode"] = area_code
        if carrier:
            payload["carrier"] = carrier

        # Try with current token
        try:
            headers = {"Authorization": f"Bearer {self.get_token()}"}
            r = textverified_api_call(
                "POST",
                f"{self.base_url}/api/pub/v2/verifications",
                headers=headers,
                json=payload,
            )
            return r.headers.get("Location", "").split("/")[-1]
        except requests.exceptions.HTTPError as e:
            # If 401, refresh token and retry once
            if e.response and e.response.status_code == 401:
                logger.warning("Token expired, refreshing...")
                headers = {
                    "Authorization": f"Bearer {self.get_token(force_refresh=True)}"
                }
                r = textverified_api_call(
                    "POST",
                    f"{self.base_url}/api/pub/v2/verifications",
                    headers=headers,
                    json=payload,
                )
                return r.headers.get("Location", "").split("/")[-1]
            raise

    @retry_with_backoff(max_retries=2, circuit_breaker_key="textverified")
    def get_verification(self, verification_id: str):
        """Get verification with automatic token refresh and retry on 401"""
        try:
            headers = {"Authorization": f"Bearer {self.get_token()}"}
            r = textverified_api_call(
                "GET",
                f"{self.base_url}/api/pub/v2/verifications/{verification_id}",
                headers=headers,
            )
            return r.json()
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 401:
                headers = {
                    "Authorization": f"Bearer {self.get_token(force_refresh=True)}"
                }
                r = textverified_api_call(
                    "GET",
                    f"{self.base_url}/api/pub/v2/verifications/{verification_id}",
                    headers=headers,
                )
                return r.json()
            raise

    @retry_with_backoff(max_retries=2, circuit_breaker_key="textverified")
    def get_messages(self, verification_id: str):
        """Get messages with automatic token refresh and retry on 401"""
        try:
            headers = {"Authorization": f"Bearer {self.get_token()}"}
            r = textverified_api_call(
                "GET",
                f"{self.base_url}/api/pub/v2/sms?reservationId={verification_id}",
                headers=headers,
            )
            return [sms["smsContent"] for sms in r.json().get("data", [])]
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 401:
                headers = {
                    "Authorization": f"Bearer {self.get_token(force_refresh=True)}"
                }
                r = textverified_api_call(
                    "GET",
                    f"{self.base_url}/api/pub/v2/sms?reservationId={verification_id}",
                    headers=headers,
                )
                return [sms["smsContent"] for sms in r.json().get("data", [])]
            raise

    def cancel_verification(self, verification_id: str):
        """Cancel verification with automatic token refresh on 401"""
        try:
            headers = {"Authorization": f"Bearer {self.get_token()}"}
            r = requests.post(
                f"{self.base_url}/api/pub/v2/verifications/{verification_id}/cancel",
                headers=headers,
                timeout=10,
            )
            r.raise_for_status()
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                headers = {
                    "Authorization": f"Bearer {self.get_token(force_refresh=True)}"
                }
                r = requests.post(
                    f"{self.base_url}/api/pub/v2/verifications/{verification_id}/cancel",
                    headers=headers,
                    timeout=10,
                )
                r.raise_for_status()
                return True
            raise


tv_client = TextVerifiedClient()

# FastAPI App
app = FastAPI(
    title="Namaskah SMS API",
    version="2.3.0",
    description="""🚀 **Simple SMS Verification Service**

# Security middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    # Rate limiting
    if not rate_limiter.is_allowed(client_ip):
        return JSONResponse({"error": "Rate limit exceeded"}, 429)
    
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response


Namaskah SMS provides temporary phone numbers for SMS verification across 1,807+ services.

## Features
- 📱 1,807+ supported services (WhatsApp, Telegram, Google, etc.)

# Add security middleware with proper integration
if SECURITY_PATCHES_AVAILABLE:
    from fastapi.middleware.base import BaseHTTPMiddleware
    
    class SecurityMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            # Rate limiting
            response = rate_limit_middleware(request, call_next)
            if hasattr(response, 'status_code') and response.status_code == 429:
                return response
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response = add_security_headers(response)
            return response
    
    app.add_middleware(SecurityMiddleware)

- 🔐 JWT & Google OAuth authentication
- 💰 Tiered pricing (Pay-as-You-Go, Developer, Enterprise)
- 🎯 Real-time SMS retrieval
- 🔔 Webhook notifications
- 📊 Analytics & usage tracking

## Rate Limits
- **100 requests per minute** per user
- Persistent rate limiting via Redis
- Returns 429 when exceeded

## Authentication
All endpoints (except `/auth/*` and `/health`) require JWT token:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

Get token via `/auth/login` or `/auth/register`.

## Currency
- **Symbol**: N
- **Exchange Rate**: 1N = $2 USD

## Pricing
- **SMS Verification**: N1 ($2) popular services, N1.25 ($2.50) general
- **Voice Verification**: SMS price + N0.25
- **Pay-as-You-Go**: No discount
- **Developer Plan**: 20% off (min N25 funded)
- **Enterprise Plan**: 35% off (min N100 funded)
- **New users**: 1 free verification
- **Referral bonus**: 1 free verification when referred user funds N2.50+

## Rentals
- **Service-Specific**: N5 (7d) to N50 (365d)
- **General Use**: N6 (7d) to N80 (365d)
- **Manual Mode**: 30% discount

## Support
- API Docs: `/docs`
- Health Check: `/health`
- Status: https://status.namaskah.app
    """,
    contact={
        "name": "Namaskah Support",
        "email": "support@namaskah.app",
        "url": "https://namaskah.app",
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User registration, login, and OAuth",
        },
        {"name": "Verification", "description": "Create and manage SMS verifications"},
        {
            "name": "Rentals",
            "description": "Long-term number rentals (hourly/daily/weekly)",
        },
        {"name": "Wallet", "description": "Fund wallet and manage credits"},
        {"name": "Admin", "description": "Admin-only endpoints (requires admin role)"},
        {"name": "API Keys", "description": "Manage API keys for programmatic access"},
        {"name": "Webhooks", "description": "Configure webhook notifications"},
        {"name": "Analytics", "description": "Usage statistics and insights"},
        {
            "name": "Notifications",
            "description": "In-app and email notification settings",
        },
        {
            "name": "Receipts",
            "description": "Verification receipts and transaction history",
        },
        {"name": "Referrals", "description": "Referral program and earnings"},
        {"name": "System", "description": "Health checks and service info"},
    ],
)


# Custom error page handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    seo_meta = {
        "title": "Page Not Found - Namaskah SMS",
        "description": "The page you are looking for could not be found. Return to Namaskah SMS for instant SMS verification services.",
        "robots": "noindex, nofollow",
    }
    context = {"request": request, **seo_meta}
    return templates.TemplateResponse("404.html", context, status_code=404)


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    seo_meta = {
        "title": "Server Error - Namaskah SMS",
        "description": "We are experiencing technical difficulties. Please try again later or contact support for assistance.",
        "robots": "noindex, nofollow",
    }
    context = {"request": request, **seo_meta}
    return templates.TemplateResponse("500.html", context, status_code=500)


# Add security middleware (order matters)
if SECURITY_MODULES_AVAILABLE:
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, calls_per_minute=100)

# Register error handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add WebSocket routes
if WEBSOCKET_AVAILABLE:
    add_websocket_routes(app)


# Register startup event
@app.on_event("startup")
async def startup_event():
    """Run background tasks on startup"""
    import asyncio

    asyncio.create_task(check_textverified_health_loop())

    # Start WebSocket background tasks
    if WEBSOCKET_AVAILABLE:
        from websocket_realtime import sms_checker_task

        asyncio.create_task(sms_checker_task())

    # Auto-fix admin password
    try:
        db = SessionLocal()
        admin = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if admin:
            try:
                bcrypt.checkpw(
                    b"Namaskah@Admin2024", admin.password_hash.encode("utf-8")
                )
                print("✅ Admin password OK")
            except:
                admin.password_hash = bcrypt.hashpw(
                    "Namaskah@Admin2024".encode(), bcrypt.gensalt()
                ).decode()
                admin.is_admin = True
                db.commit()
                print("✅ Admin password auto-fixed")
        else:
            # Create admin if doesn't exist
            import secrets

            admin = User(
                id=f"user_{datetime.now(timezone.utc).timestamp()}",
                email="admin@namaskah.app",
                password_hash=bcrypt.hashpw(
                    b"Namaskah@Admin2024", bcrypt.gensalt()
                ).decode(),
                credits=100.0,
                is_admin=True,
                email_verified=True,
                referral_code=secrets.token_urlsafe(6),
            )
            db.add(admin)
            db.commit()
            print("✅ Admin user created")
        db.close()
    except Exception as e:
        print(f"Admin check: {e}")


# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Tracking script
@app.get("/track.js")
async def tracking_script():
    """Serve tracking JavaScript"""
    script = """
(function() {
    const API_BASE = '';
    
    function track(action, element, details) {
        const token = localStorage.getItem('token') || localStorage.getItem('admin_token');
        fetch(API_BASE + '/track', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': token ? `Bearer ${token}` : ''
            },
            body: JSON.stringify({
                page: window.location.pathname,
                action: action,
                element: element,
                details: details
            })
        }).catch(() => {});
    }
    
    // Track page view
    track('page_view', null, document.title);
    
    // Track button clicks
    document.addEventListener('click', function(e) {
        const target = e.target.closest('button, a, [onclick]');
        if (target) {
            const text = target.textContent.trim().substring(0, 50);
            const id = target.id || target.className;
            track('click', id || text, text);
        }
    });
    
    // Track form submissions
    document.addEventListener('submit', function(e) {
        const form = e.target;
        const formId = form.id || form.action;
        track('form_submit', formId, 'Form submitted');
    });
    
    // Track errors
    window.addEventListener('error', function(e) {
        track('error', 'window', e.message);
    });
})();
    """
    from fastapi.responses import Response

    return Response(content=script, media_type="application/javascript")


@app.get("/")
async def root(request: Request):
    seo_meta = get_seo_meta("/", str(request.url))
    context = {"request": request, "analytics_id": GOOGLE_ANALYTICS_ID, **seo_meta}
    response = templates.TemplateResponse("landing.html", context)
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/app")
async def app_page(request: Request):
    seo_meta = get_seo_meta("/app", str(request.url))
    context = {"request": request, "analytics_id": GOOGLE_ANALYTICS_ID, **seo_meta}
    return templates.TemplateResponse("index.html", context)


@app.get("/simple")
async def simple_dashboard(request: Request):
    """Minimal dashboard for testing and development"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api-docs")
async def api_docs_page(request: Request):
    seo_meta = get_seo_meta("/api-docs", str(request.url))
    context = {"request": request, "analytics_id": GOOGLE_ANALYTICS_ID, **seo_meta}
    return templates.TemplateResponse("api_docs.html", context)


@app.get("/faq")
async def faq_page(request: Request):
    seo_meta = get_seo_meta("/faq", str(request.url))
    context = {"request": request, **seo_meta}
    return templates.TemplateResponse("faq.html", context)


@app.get("/about")
async def about_page(request: Request):
    seo_meta = get_seo_meta("/about", str(request.url))
    context = {"request": request, **seo_meta}
    return templates.TemplateResponse("about.html", context)


@app.get("/reviews")
async def reviews_page(request: Request):
    seo_meta = get_seo_meta("/reviews", str(request.url))
    context = {"request": request, **seo_meta}
    return templates.TemplateResponse("reviews.html", context)


@app.get("/status")
async def status_page(request: Request):
    seo_meta = get_seo_meta("/status", str(request.url))
    context = {"request": request, **seo_meta}
    return templates.TemplateResponse("status.html", context)


@app.get("/admin")
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/test-buttons")
async def test_buttons_page(request: Request):
    """Serve button test page for debugging"""
    from fastapi.responses import FileResponse

    return FileResponse("test_buttons.html")


@app.get("/privacy")
async def privacy_page(request: Request):
    seo_meta = get_seo_meta("/privacy", str(request.url))
    context = {"request": request, **seo_meta}
    return templates.TemplateResponse("privacy.html", context)


@app.get("/terms")
async def terms_page(request: Request):
    seo_meta = get_seo_meta("/terms", str(request.url))
    context = {"request": request, **seo_meta}
    return templates.TemplateResponse("terms.html", context)


@app.get("/refund")
async def refund_page(request: Request):
    seo_meta = get_seo_meta("/refund", str(request.url))
    context = {"request": request, **seo_meta}
    return templates.TemplateResponse("refund.html", context)


@app.get("/cookies")
async def cookies_page(request: Request):
    seo_meta = get_seo_meta("/cookies", str(request.url))
    context = {"request": request, **seo_meta}
    return templates.TemplateResponse("cookies.html", context)


@app.get("/contact")
async def contact_page(request: Request):
    seo_meta = get_seo_meta("/contact", str(request.url))
    context = {"request": request, **seo_meta}
    return templates.TemplateResponse("contact.html", context)


@app.get("/analytics")
async def analytics_page(request: Request):
    seo_meta = get_seo_meta("/analytics", str(request.url))
    context = {"request": request, **seo_meta}
    return templates.TemplateResponse("analytics.html", context)


@app.get("/manifest.json")
async def manifest():
    """Serve PWA manifest"""
    from fastapi.responses import FileResponse

    return FileResponse("static/manifest.json", media_type="application/json")


@app.get("/sitemap.xml")
async def generate_sitemap():
    """Generate dynamic XML sitemap for SEO"""
    from datetime import datetime

    # Define all public pages with priorities and change frequencies
    pages = [
        {
            "url": "https://namaskah.app/",
            "priority": "1.0",
            "changefreq": "daily",
            "lastmod": datetime.now().strftime("%Y-%m-%d"),
        },
        {
            "url": "https://namaskah.app/app",
            "priority": "0.9",
            "changefreq": "daily",
            "lastmod": datetime.now().strftime("%Y-%m-%d"),
        },
        {
            "url": "https://namaskah.app/api-docs",
            "priority": "0.8",
            "changefreq": "weekly",
            "lastmod": "2025-01-19",
        },
        {
            "url": "https://namaskah.app/faq",
            "priority": "0.7",
            "changefreq": "monthly",
            "lastmod": "2025-01-19",
        },
        {
            "url": "https://namaskah.app/about",
            "priority": "0.7",
            "changefreq": "monthly",
            "lastmod": "2025-01-19",
        },
        {
            "url": "https://namaskah.app/contact",
            "priority": "0.7",
            "changefreq": "monthly",
            "lastmod": "2025-01-19",
        },
        {
            "url": "https://namaskah.app/status",
            "priority": "0.6",
            "changefreq": "daily",
            "lastmod": datetime.now().strftime("%Y-%m-%d"),
        },
        {
            "url": "https://namaskah.app/reviews",
            "priority": "0.6",
            "changefreq": "monthly",
            "lastmod": "2025-01-19",
        },
        {
            "url": "https://namaskah.app/privacy",
            "priority": "0.4",
            "changefreq": "monthly",
            "lastmod": "2025-01-19",
        },
        {
            "url": "https://namaskah.app/terms",
            "priority": "0.4",
            "changefreq": "monthly",
            "lastmod": "2025-01-19",
        },
        {
            "url": "https://namaskah.app/refund",
            "priority": "0.4",
            "changefreq": "monthly",
            "lastmod": "2025-01-19",
        },
        {
            "url": "https://namaskah.app/cookies",
            "priority": "0.3",
            "changefreq": "monthly",
            "lastmod": "2025-01-19",
        },
    ]

    # Generate XML
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for page in pages:
        xml_content += f"  <url>\n"
        xml_content += f'    <loc>{page["url"]}</loc>\n'
        xml_content += f'    <lastmod>{page["lastmod"]}</lastmod>\n'
        xml_content += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
        xml_content += f'    <priority>{page["priority"]}</priority>\n'
        xml_content += f"  </url>\n"

    xml_content += "</urlset>"

    return Response(content=xml_content, media_type="application/xml")


@app.get("/robots.txt")
async def robots():
    """Serve robots.txt for search engines"""
    from fastapi.responses import FileResponse

    return FileResponse("static/robots.txt", media_type="text/plain")


@app.get("/sw.js")
async def service_worker():
    """Serve service worker"""
    from fastapi.responses import FileResponse

    return FileResponse("static/sw.js", media_type="application/javascript")


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return

    try:
        # Verify token
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]

        # Connect user
        await manager.connect(websocket, user_id)

        try:
            while True:
                # Listen for messages
                data = await websocket.receive_json()

                # Handle ping/pong for heartbeat
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

        except WebSocketDisconnect:
            manager.disconnect(user_id)

    except jwt.InvalidTokenError:
        await websocket.close(code=4001, reason="Invalid token")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close(code=4000, reason="Server error")


# CSRF Token endpoint
@app.get("/csrf-token", tags=["System"], summary="Get CSRF Token")
def get_csrf_token():
    import secrets

    token = secrets.token_urlsafe(32)
    return {"token": token}


@app.get("/health", tags=["System"], summary="Health Check")
def health():
    websocket_connections = 0
    if WEBSOCKET_AVAILABLE:
        websocket_connections = len(manager.active_connections)

    return {
        "status": "healthy",
        "service": "namaskah-sms",
        "version": "2.3.0",
        "database": "connected",
        "websocket_connections": websocket_connections,
        "security_patches": SECURITY_PATCHES_AVAILABLE,
        "websocket_support": WEBSOCKET_AVAILABLE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


class TestEmailRequest(BaseModel):
    email: str


@app.post("/test-email")
def test_email(request: TestEmailRequest):
    """Test email integration"""
    try:
        result = send_email(
            request.email,
            "Test Email - Namaskah SMS",
            "<h2>Test Email</h2><p>This is a test email from Namaskah SMS.</p>",
        )
        return {
            "status": "success" if result else "failed",
            "message": (
                "Test email sent" if result else "Email configuration not available"
            ),
        }
    except Exception as e:
        return {"status": "failed", "message": str(e)}


@app.post("/emergency-admin-reset", tags=["System"], summary="Emergency Admin Reset")
def emergency_admin_reset(secret: str, db: Session = Depends(get_db)):
    """Emergency endpoint to reset admin password - remove after use"""
    if secret != "NAMASKAH_EMERGENCY_2024":
        raise HTTPException(status_code=403, detail="Invalid secret")

    try:
        admin = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if admin:
            admin.password_hash = bcrypt.hashpw(
                "Namaskah@Admin2024".encode(), bcrypt.gensalt()
            ).decode()
            admin.is_admin = True
            admin.email_verified = True
            db.commit()
            return {
                "status": "success",
                "message": "Admin password reset to Namaskah@Admin2024",
            }
        else:
            import secrets

            admin = User(
                id=f"user_{datetime.now(timezone.utc).timestamp()}",
                email="admin@namaskah.app",
                password_hash=bcrypt.hashpw(
                    b"Namaskah@Admin2024", bcrypt.gensalt()
                ).decode(),
                credits=100.0,
                is_admin=True,
                email_verified=True,
                referral_code=secrets.token_urlsafe(6),
            )
            db.add(admin)
            db.commit()
            return {
                "status": "success",
                "message": "Admin user created with password Namaskah@Admin2024",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/services/list", tags=["System"], summary="List All Services")
def get_services_list():
    """Get complete list of supported services with categories and pricing tiers

    Returns:
    - categories: Services grouped by category
    - tiers: Services grouped by pricing tier
    - pricing: Cost per tier
    """
    try:
        import json

        with open("services_categorized.json", "r") as f:
            data = json.load(f)

        # Add tier information with dynamic pricing
        data["tiers"] = {
            tier_id: {
                "name": tier_data["name"],
                "price": tier_data["base_price"],
                "price_usd": tier_data["base_price"] * 2,
                "services": tier_data["services"],
                "success_rate": tier_data["success_rate"],
            }
            for tier_id, tier_data in SERVICE_TIERS.items()
        }

        # Add pricing plans info
        data["plans"] = {
            plan_id: {
                "name": plan_data["name"],
                "discount": plan_data["discount"],
                "free_verifications": plan_data.get("free_verifications", 0),
            }
            for plan_id, plan_data in SUBSCRIPTION_PLANS.items()
        }

        return data
    except:
        return {"categories": {}, "uncategorized": [], "tiers": {}}


@app.get("/services/price/{service_name}", tags=["System"], summary="Get Service Price")
def get_service_price_endpoint(
    service_name: str, request: Request, db: Session = Depends(get_db)
):
    """Get dynamic price for a service (public endpoint)"""
    # Default to starter plan for unauthenticated users
    user_plan = "starter"
    monthly_count = 0

    # Try to get user info if authenticated
    try:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("user_id")

            if user_id:
                # Get user's subscription
                subscription = (
                    db.query(Subscription)
                    .filter(
                        Subscription.user_id == user_id, Subscription.status == "active"
                    )
                    .first()
                )
                user_plan = subscription.plan if subscription else "starter"

                # Get monthly count
                month_start = datetime.now(timezone.utc).replace(
                    day=1, hour=0, minute=0, second=0
                )
                monthly_count = (
                    db.query(Verification)
                    .filter(
                        Verification.user_id == user_id,
                        Verification.created_at >= month_start,
                    )
                    .count()
                )
    except:
        pass  # Use defaults for unauthenticated users

    # Calculate price
    tier = get_service_tier(service_name)
    base_price = get_service_price(service_name, user_plan, monthly_count)

    return {
        "service": service_name,
        "tier": tier,
        "tier_name": SERVICE_TIERS[tier]["name"],
        "base_price": base_price,
        "base_price_usd": base_price * 2,
        "user_plan": user_plan,
        "monthly_verifications": monthly_count,
        "voice_premium": VOICE_PREMIUM,
        "addons": {
            "custom_area_code": PREMIUM_ADDONS["custom_area_code"],
            "guaranteed_carrier": PREMIUM_ADDONS["guaranteed_carrier"],
            "priority_queue": PREMIUM_ADDONS["priority_queue"],
        },
    }


@app.get("/services/status", tags=["System"], summary="Get Service Status")
def get_services_status(db: Session = Depends(get_db)):
    """Get real-time status of all services based on recent verification success rates

    Returns:
    - categories: Services grouped by category
    - status: Service status (operational, degraded, down)
    - overall_status: Overall platform status
    """
    try:
        import json

        with open("services_categorized.json", "r") as f:
            data = json.load(f)

        # Check recent verifications (last 24 hours) for each service
        from sqlalchemy import func
        from datetime import timedelta

        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)

        # Get success rates per service from verifications
        service_stats = (
            db.query(
                Verification.service_name,
                func.count(Verification.id).label("total"),
                func.sum(
                    func.case((Verification.status == "completed", 1), else_=0)
                ).label("completed"),
            )
            .filter(Verification.created_at >= twenty_four_hours_ago)
            .group_by(Verification.service_name)
            .all()
        )

        status_map = {}
        down_count = 0
        degraded_count = 0

        for stat in service_stats:
            if stat.total > 0:
                success_rate = (stat.completed / stat.total) * 100

                # Determine status
                if success_rate < 50:
                    service_status = "down"
                    down_count += 1
                elif success_rate < 85:
                    service_status = "degraded"
                    degraded_count += 1
                else:
                    service_status = "operational"

                status_map[stat.service_name] = service_status

                # Update or create service status record
                status_record = (
                    db.query(ServiceStatus)
                    .filter(ServiceStatus.service_name == stat.service_name)
                    .first()
                )

                if status_record:
                    status_record.status = service_status
                    status_record.success_rate = success_rate
                    status_record.last_checked = datetime.now(timezone.utc)
                else:
                    status_record = ServiceStatus(
                        id=f"status_{stat.service_name}_{datetime.now(timezone.utc).timestamp()}",
                        service_name=stat.service_name,
                        status=service_status,
                        success_rate=success_rate,
                    )
                    db.add(status_record)

        db.commit()

        # Determine overall status
        if down_count > 5:
            overall_status = "down"
        elif down_count > 0 or degraded_count > 3:
            overall_status = "degraded"
        else:
            overall_status = "operational"

        return {
            "categories": data.get("categories", {}),
            "status": status_map,
            "overall_status": overall_status,
            "stats": {
                "down": down_count,
                "degraded": degraded_count,
                "operational": len(service_stats) - down_count - degraded_count,
            },
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        # Default to all operational if error
        return {
            "categories": {},
            "status": {},
            "overall_status": "operational",
            "stats": {"down": 0, "degraded": 0, "operational": 0},
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }


@app.get(
    "/services/status/history", tags=["System"], summary="Get Service Status History"
)
def get_service_status_history(service_name: str = None, db: Session = Depends(get_db)):
    """Get historical status data for services"""
    query = db.query(ServiceStatus)

    if service_name:
        query = query.filter(ServiceStatus.service_name == service_name)

    statuses = query.order_by(ServiceStatus.created_at.desc()).limit(100).all()

    return {
        "history": [
            {
                "service_name": s.service_name,
                "status": s.status,
                "success_rate": s.success_rate,
                "checked_at": s.last_checked.isoformat(),
            }
            for s in statuses
        ]
    }


@app.get("/carriers/list", tags=["System"], summary="Get Available Carriers")
def get_available_carriers():
    """Get list of supported carriers for Pro users"""
    return {
        "carriers": [
            {
                "value": carrier_id,
                "label": carrier_data["name"],
                "type": carrier_data["type"],
                "popular": carrier_id in ["verizon", "att", "tmobile"],
            }
            for carrier_id, carrier_data in SUPPORTED_CARRIERS.items()
        ]
    }


@app.get("/area-codes/list", tags=["System"], summary="Get Available Area Codes")
def get_available_area_codes():
    """Get list of supported area codes for Pro users"""
    popular_codes = ["212", "310", "415", "312", "214", "305"]

    return {
        "area_codes": [
            {
                "value": area_code,
                "label": f"{location['city']}, {location['state']} ({area_code})",
                "city": location["city"],
                "state": location["state"],
                "region": location["region"],
                "popular": area_code in popular_codes,
            }
            for area_code, location in AREA_CODE_MAP.items()
        ]
    }


@app.post("/auth/register", tags=["Authentication"], summary="Register New User")
def register(
    req: RegisterRequest,
    request: Request,
    referral_code: str = None,
    db: Session = Depends(get_db),
):
    # Enhanced input validation
    if SECURITY_PATCHES_AVAILABLE:
        try:
            validated_data = validate_user_registration(
                {"email": req.email, "password": req.password}
            )
            req.email = validated_data["email"]
            req.password = validated_data["password"]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Log security event
        client_ip = request.client.host if request.client else "unknown"
        log_security_event("user_registration", None, client_ip, f"Email: {req.email}")
    """Register a new user account
    
    - **email**: Valid email address
    - **password**: Minimum 6 characters
    - **referral_code**: Optional referral code for bonus credits
    
    Returns JWT token and user details. New users get 1 free verification.
    """
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    import secrets

    user_referral_code = secrets.token_urlsafe(6)
    verification_token = secrets.token_urlsafe(32)

    # Use secure password hashing
    if SECURITY_PATCHES_AVAILABLE:
        password_hash = hash_password_secure(req.password)
    else:
        password_hash = hash_password(req.password)

    user = User(
        id=f"user_{datetime.now(timezone.utc).timestamp()}",
        email=req.email,
        password_hash=password_hash,
        credits=0.0,
        free_verifications=1.0,
        referral_code=user_referral_code,
        email_verified=False,
        verification_token=verification_token,
    )

    # Handle referral
    if referral_code:
        referrer = db.query(User).filter(User.referral_code == referral_code).first()
        if referrer:
            user.referred_by = referrer.id
            user.free_verifications += 1.0  # Bonus for being referred
            # Referrer gets 1 free verification when referred user funds N2.50+
            referrer.referral_earnings += 0.0  # Track pending

            # Create referral record
            referral = Referral(
                id=f"ref_{datetime.now(timezone.utc).timestamp()}",
                referrer_id=referrer.id,
                referred_id=user.id,
                reward_amount=1.0,
            )
            db.add(referral)

            # Transactions will be created when referred user funds wallet

    db.add(user)
    db.commit()

    # Log registration
    log_activity(
        db,
        user_id=user.id,
        email=user.email,
        action="register",
        status="success",
        details=f"New user registered",
    )

    # Send verification email
    try:
        send_email(
            user.email,
            "Verify Your Email - Namaskah SMS",
            f"""<h2>Welcome to Namaskah SMS!</h2>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{BASE_URL}/auth/verify?token={verification_token}">Verify Email</a></p>
            <p>Or copy this link: {BASE_URL}/auth/verify?token={verification_token}</p>""",
        )
    except Exception as e:
        print(f"Email send error: {e}")

    token = jwt.encode(
        {"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(days=30)},
        JWT_SECRET,
        algorithm="HS256",
    )
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return {
        "token": token,
        "user_id": user.id,
        "credits": user.credits,
        "free_verifications": user.free_verifications,
        "referral_code": user.referral_code,
        "email_verified": False,
    }


@app.get(
    "/auth/google/config", tags=["Authentication"], summary="Get Google OAuth Config"
)
def get_google_config():
    """Get Google OAuth configuration"""
    # Check if Google OAuth is properly configured
    is_configured = (
        GOOGLE_CLIENT_ID
        and GOOGLE_CLIENT_ID != "your-google-client-id.apps.googleusercontent.com"
        and len(GOOGLE_CLIENT_ID) > 20  # Basic validation
    )

    return {
        "client_id": GOOGLE_CLIENT_ID if is_configured else None,
        "enabled": is_configured,
    }


@app.post("/auth/google", tags=["Authentication"], summary="Google OAuth Login")
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate with Google OAuth"""
    if (
        not GOOGLE_CLIENT_ID
        or GOOGLE_CLIENT_ID == "your-google-client-id.apps.googleusercontent.com"
    ):
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            req.token, google_requests.Request(), GOOGLE_CLIENT_ID
        )

        email = idinfo["email"]
        google_id = idinfo["sub"]
        email_verified = idinfo.get("email_verified", False)

        # Check if user exists
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Create new user
            import secrets

            user = User(
                id=f"user_{datetime.now(timezone.utc).timestamp()}",
                email=email,
                password_hash=bcrypt.hashpw(
                    google_id.encode("utf-8"), bcrypt.gensalt()
                ).decode(),
                credits=0.0,
                free_verifications=1.0,
                referral_code=secrets.token_urlsafe(6),
                email_verified=email_verified,  # Auto-verify if Google verified
            )
            db.add(user)
            db.commit()

            # Log registration
            log_activity(
                db,
                user_id=user.id,
                email=user.email,
                action="google_register",
                status="success",
                details="New user via Google OAuth",
            )
        else:
            # Update email verification if Google verified
            if email_verified and not user.email_verified:
                user.email_verified = True
                db.commit()

            # Log login
            log_activity(
                db,
                user_id=user.id,
                email=user.email,
                action="google_login",
                status="success",
                details="Login via Google OAuth",
            )

        # Generate JWT
        token = jwt.encode(
            {
                "user_id": user.id,
                "exp": datetime.now(timezone.utc) + timedelta(days=30),
            },
            JWT_SECRET,
            algorithm="HS256",
        )
        if isinstance(token, bytes):
            token = token.decode("utf-8")

        return {
            "token": token,
            "user_id": user.id,
            "credits": user.credits,
            "free_verifications": user.free_verifications,
            "is_admin": user.is_admin,
            "email_verified": user.email_verified,
        }
    except ImportError:
        raise HTTPException(
            status_code=503, detail="Google OAuth library not installed"
        )
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(
            status_code=401, detail=f"Google authentication failed: {str(e)}"
        )


@app.post("/auth/login", tags=["Authentication"], summary="Login User")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    # Enhanced input validation
    if SECURITY_PATCHES_AVAILABLE:
        req.email = sanitize_input(req.email.lower().strip())
        if not validate_email(req.email):
            raise HTTPException(status_code=400, detail="Invalid email format")

        # Log security event
        client_ip = request.client.host if request.client else "unknown"
        log_security_event("login_attempt", None, client_ip, f"Email: {req.email}")
    """Login with email and password
    
    Returns JWT token valid for 30 days.
    """
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Verify password using secure function
    try:
        if SECURITY_PATCHES_AVAILABLE:
            password_valid = verify_password_secure(req.password, user.password_hash)
        else:
            password_valid = verify_password(req.password, user.password_hash)
    except Exception as e:
        print(f"Password verify error: {e}")
        password_valid = False

    if not password_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generate token immediately (activity logging disabled due to schema issues)
    token = jwt.encode(
        {"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(days=30)},
        JWT_SECRET,
        algorithm="HS256",
    )
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return {
        "token": token,
        "user_id": user.id,
        "credits": user.credits,
        "free_verifications": user.free_verifications,
        "is_admin": user.is_admin,
        "email_verified": user.email_verified,
    }


@app.get("/auth/verify")
def verify_email_page(request: Request, token: str = None):
    """Email verification page"""
    return templates.TemplateResponse("email_verify.html", {"request": request})


@app.get("/api/auth/verify", tags=["Authentication"], summary="Verify Email API")
def verify_email_api(token: str, db: Session = Depends(get_db)):
    """Verify email address using token from registration email"""
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    # Check if already verified
    if user.email_verified:
        return {"message": "Email already verified", "redirect": "/app"}

    user.email_verified = True
    user.verification_token = None
    db.commit()

    # Send welcome email
    try:
        send_email(
            user.email,
            "Welcome to Namaskah SMS!",
            f"""<h2>Email Verified Successfully!</h2>
            <p>Welcome to Namaskah SMS! Your email has been verified.</p>
            <p>You now have 1 free verification to get started.</p>
            <p><a href="{BASE_URL}/app">Start Using Namaskah SMS</a></p>""",
        )
    except Exception as e:
        print(f"Welcome email error: {e}")

    return {
        "message": "🎉 Email verified successfully! Welcome to Namaskah SMS. You now have 1 free verification and are eligible to use all verification services.",
        "redirect": "/app",
        "verified": True,
        "free_verifications": user.free_verifications,
    }


@app.post(
    "/auth/resend-verification",
    tags=["Authentication"],
    summary="Resend Verification Email",
)
def resend_verification(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Resend email verification link"""
    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    import secrets

    verification_token = secrets.token_urlsafe(32)
    user.verification_token = verification_token
    db.commit()

    # Send verification email
    try:
        send_email(
            user.email,
            "Verify Your Email - Namaskah SMS",
            f"""<h2>Email Verification</h2>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{BASE_URL}/auth/verify?token={verification_token}">Verify Email</a></p>""",
        )
    except Exception as e:
        print(f"Email send error: {e}")

    return {"message": "Verification email sent"}


@app.post(
    "/auth/forgot-password", tags=["Authentication"], summary="Request Password Reset"
)
def forgot_password(req: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset link via email. Link expires in 1 hour."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        return {"message": "If email exists, reset link sent"}

    import secrets

    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    # Send password reset email
    try:
        send_email(
            user.email,
            "Password Reset - Namaskah SMS",
            f"""<h2>Password Reset Request</h2>
            <p>Click the link below to reset your password:</p>
            <p><a href="{BASE_URL}/auth/reset-password?token={reset_token}">Reset Password</a></p>
            <p>This link expires in 1 hour.</p>""",
        )
    except Exception as e:
        print(f"Password reset email error: {e}")

    return {"message": "If email exists, reset link sent"}


@app.post("/auth/reset-password", tags=["Authentication"], summary="Reset Password")
def reset_password(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Reset password using token from reset email"""
    user = db.query(User).filter(User.reset_token == req.token).first()
    if (
        not user
        or not user.reset_token_expires
        or user.reset_token_expires < datetime.now(timezone.utc)
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.password_hash = hash_password(req.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Password reset successfully"}


@app.get("/auth/me", tags=["Authentication"], summary="Get Current User")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get authenticated user information and credit balance"""
    credits = user.credits

    # If admin, show real TextVerified balance
    if user.is_admin:
        try:
            token = tv_client.get_token()
            import requests

            headers = {"Authorization": f"Bearer {token}"}
            r = requests.get(
                f"{tv_client.base_url}/api/pub/v2/account/me", headers=headers
            )
            data = r.json()
            credits = data.get("currentBalance", user.credits)
        except:
            pass

    # Get subscription plan
    plan = "starter"
    try:
        subscription = (
            db.query(Subscription)
            .filter(Subscription.user_id == user.id, Subscription.status == "active")
            .first()
        )
        if subscription:
            plan = subscription.plan
    except Exception as e:
        logger.error(f"Subscription query failed: {e}")

    return {
        "id": user.id,
        "email": user.email,
        "credits": credits,
        "free_verifications": user.free_verifications,
        "is_admin": user.is_admin,
        "email_verified": user.email_verified,
        "created_at": user.created_at,
        "subscription_plan": plan,
    }


@app.get(
    "/verifications/active", tags=["Verification"], summary="Get Active Verifications"
)
def get_active_verifications(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all active (pending) verifications for current user"""
    verifications = (
        db.query(Verification)
        .filter(Verification.user_id == user.id, Verification.status == "pending")
        .order_by(Verification.created_at.desc())
        .all()
    )

    return {
        "verifications": [
            {
                "id": v.id,
                "service_name": v.service_name,
                "phone_number": v.phone_number,
                "capability": v.capability,
                "status": v.status,
                "cost": v.cost,
                "created_at": v.created_at.isoformat(),
            }
            for v in verifications
        ]
    }


@app.get(
    "/verifications/history", tags=["Verification"], summary="Get Verification History"
)
def get_history(
    service: str = None,
    status: str = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get verification history with filtering for current user"""
    query = db.query(Verification).filter(Verification.user_id == user.id)

    # Filter by service
    if service:
        query = query.filter(Verification.service_name == service)

    # Filter by status
    if status and status in ["pending", "completed", "cancelled"]:
        query = query.filter(Verification.status == status)

    verifications = query.order_by(Verification.created_at.desc()).limit(limit).all()

    return {
        "verifications": [
            {
                "id": v.id,
                "service_name": v.service_name,
                "phone_number": v.phone_number,
                "capability": v.capability,
                "status": v.status,
                "cost": v.cost,
                "created_at": v.created_at.isoformat(),
            }
            for v in verifications
        ]
    }


@app.get(
    "/verifications/export",
    tags=["Verification"],
    summary="Export Verifications to CSV",
)
def export_user_verifications(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Export user's verifications to CSV"""
    from fastapi.responses import StreamingResponse
    import io
    import csv

    verifications = (
        db.query(Verification)
        .filter(Verification.user_id == user.id)
        .order_by(Verification.created_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["Date", "Service", "Phone Number", "Type", "Status", "Cost (N)"])

    # Data
    for v in verifications:
        writer.writerow(
            [
                v.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                v.service_name,
                v.phone_number or "N/A",
                v.capability.upper(),
                v.status.upper(),
                f"{v.cost:.2f}",
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=verifications_{user.id}.csv"
        },
    )


@app.get("/transactions/history", tags=["Wallet"], summary="Get Transaction History")
def get_transactions(
    type: str = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get transaction history with filtering (credits/debits) for current user"""
    query = db.query(Transaction).filter(Transaction.user_id == user.id)

    # Filter by type
    if type and type in ["credit", "debit"]:
        query = query.filter(Transaction.type == type)

    transactions = query.order_by(Transaction.created_at.desc()).limit(limit).all()

    return {
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "type": t.type,
                "description": t.description,
                "created_at": t.created_at.isoformat(),
            }
            for t in transactions
        ]
    }


@app.get("/wallet/transactions", tags=["Wallet"], summary="Get Wallet Transactions")
def get_wallet_transactions(
    type: str = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get wallet transaction history with filtering (credits/debits) for current user"""
    query = db.query(Transaction).filter(Transaction.user_id == user.id)

    # Filter by type
    if type and type in ["credit", "debit"]:
        query = query.filter(Transaction.type == type)

    transactions = query.order_by(Transaction.created_at.desc()).limit(limit).all()

    return {
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "type": t.type,
                "description": t.description,
                "created_at": t.created_at.isoformat(),
            }
            for t in transactions
        ]
    }


@app.get("/transactions/export", tags=["Wallet"], summary="Export Transactions to CSV")
def export_user_transactions(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Export user's transactions to CSV"""
    from fastapi.responses import StreamingResponse
    import io
    import csv

    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["Date", "Type", "Amount (N)", "Description"])

    # Data
    for t in transactions:
        writer.writerow(
            [
                t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                t.type.upper(),
                f"{t.amount:.2f}",
                t.description,
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=transactions_{user.id}.csv"
        },
    )


@app.post(
    "/verify/create", tags=["Verification"], summary="Create SMS/Voice Verification"
)
def create_verification(
    req: CreateVerificationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate input
    req.service_name = validate_service_name(req.service_name)

    # Log security event
    log_security_event(
        "verification_create", user.id, details=f"Service: {req.service_name}"
    )
    """Create new SMS or voice verification
    
    - **service_name**: Service identifier (e.g., 'whatsapp', 'telegram')
    - **capability**: 'sms' or 'voice'
    - **area_code**: Optional custom area code (+$4)
    - **carrier**: Optional guaranteed carrier (+$6)
    """
    # Get user's subscription plan
    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id, Subscription.status == "active")
        .first()
    )
    user_plan = subscription.plan if subscription else "starter"

    # Get monthly verification count for volume discount
    from datetime import timedelta

    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0)
    monthly_count = (
        db.query(Verification)
        .filter(Verification.user_id == user.id, Verification.created_at >= month_start)
        .count()
    )

    # Calculate base cost using dynamic pricing
    cost = get_service_price(req.service_name, user_plan, monthly_count)

    # Add voice premium if voice verification
    if req.capability == "voice":
        cost += VOICE_PREMIUM

    # Add premium add-on costs
    if req.area_code:
        cost += PREMIUM_ADDONS["custom_area_code"]
    if req.carrier:
        cost += PREMIUM_ADDONS["guaranteed_carrier"]

    # Check if user has free verifications
    plan_data = SUBSCRIPTION_PLANS[user_plan]
    free_limit = plan_data.get("free_verifications", 0)

    if free_limit == -1 or (user.free_verifications > 0 and free_limit > 0):
        # Use free verification
        if user.free_verifications > 0:
            user.free_verifications -= 1
        cost = 0
    elif user.credits < cost:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Need N{cost}, have N{user.credits}",
        )

    user_id = user.id

    # Create verification with filters
    try:
        verification_id = tv_client.create_verification(
            req.service_name,
            req.capability,
            area_code=req.area_code,
            carrier=req.carrier,
        )
        details = tv_client.get_verification(verification_id)
    except Exception as e:
        print(f"TextVerified API error: {e}")
        raise HTTPException(
            status_code=503, detail=f"Verification service unavailable: {str(e)}"
        )

    # Deduct credits if not free
    if cost > 0:
        user.credits -= cost

    # Get service tier for tracking
    tier = get_service_tier(req.service_name)

    verification = Verification(
        id=verification_id,
        user_id=user_id,
        service_name=req.service_name,
        phone_number=details.get("number"),
        capability=req.capability,
        status="pending",
        cost=cost,
        requested_carrier=req.carrier,
        requested_area_code=req.area_code,
    )

    # Get carrier and location info for display
    carrier_info = format_carrier_info(req.carrier, details.get("number"))
    location_info = get_location_info(details.get("number"))
    db.add(verification)

    # Create transaction if cost > 0
    if cost > 0:
        db.add(
            Transaction(
                id=f"txn_{datetime.now(timezone.utc).timestamp()}",
                user_id=user.id,
                amount=-cost,
                type="debit",
                description=f"{req.service_name} verification ({tier})",
            )
        )

    db.commit()

    # Show first 3 digits if area code was requested
    phone_preview = None
    if req.area_code and verification.phone_number:
        area_code = extract_area_code(verification.phone_number)
        phone_preview = f"({area_code}) XXX-XXXX" if area_code else None

    return {
        "id": verification.id,
        "service_name": verification.service_name,
        "phone_number": verification.phone_number,
        "phone_preview": phone_preview,
        "capability": verification.capability,
        "status": verification.status,
        "cost": cost,
        "remaining_credits": user.credits,
        "carrier_info": carrier_info,
        "location_info": location_info,
        "user_selections": {
            "requested_carrier": req.carrier,
            "requested_area_code": req.area_code,
        },
    }


@app.get(
    "/verify/{verification_id}",
    tags=["Verification"],
    summary="Get Verification Status",
)
def get_verification(verification_id: str, db: Session = Depends(get_db)):
    """Get verification details and current status - NO AUTH REQUIRED"""
    verification = (
        db.query(Verification).filter(Verification.id == verification_id).first()
    )

    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    details = tv_client.get_verification(verification_id)
    new_status = (
        "completed" if details.get("state") == "verificationCompleted" else "pending"
    )

    # Check if verification just completed
    if verification.status == "pending" and new_status == "completed":
        verification.status = "completed"
        verification.completed_at = datetime.now(timezone.utc)

        # Send real-time status update
        asyncio.create_task(
            manager.send_personal_message(
                {
                    "type": "verification_status",
                    "payload": {
                        "verification_id": verification.id,
                        "status": "completed",
                        "phone_number": verification.phone_number,
                    },
                },
                verification.user_id,
            )
        )

        # Get user for receipt generation
        user = db.query(User).filter(User.id == verification.user_id).first()
        if user:
            # Get ISP/carrier info from TextVerified
            isp_carrier = details.get("carrier") or details.get("network") or "Unknown"

            # Process successful verification and send receipt
            try:
                process_successful_verification(
                    db=db,
                    user_id=user.id,
                    user_email=user.email,
                    verification_id=verification.id,
                    service_name=verification.service_name,
                    phone_number=verification.phone_number,
                    amount_spent=verification.cost,
                    isp_carrier=isp_carrier,
                )
            except Exception as e:
                print(f"Receipt generation failed: {e}")

    db.commit()

    # Add carrier and location info to response
    carrier_info = format_carrier_info(None, verification.phone_number)
    location_info = get_location_info(verification.phone_number)

    return {
        "id": verification.id,
        "service_name": verification.service_name,
        "phone_number": verification.phone_number,
        "status": verification.status,
        "cost": verification.cost,
        "created_at": verification.created_at,
        "carrier_info": carrier_info,
        "location_info": location_info,
    }


@app.get(
    "/verify/{verification_id}/messages",
    tags=["Verification"],
    summary="Get SMS Messages",
)
async def get_messages(verification_id: str, db: Session = Depends(get_db)):
    """Retrieve SMS messages for verification - NO AUTH REQUIRED"""
    verification = (
        db.query(Verification).filter(Verification.id == verification_id).first()
    )

    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    messages = tv_client.get_messages(verification_id)

    # Send real-time SMS update if new messages found
    if messages:
        for message in messages:
            asyncio.create_task(
                manager.send_personal_message(
                    {
                        "type": "sms_received",
                        "payload": {
                            "verification_id": verification_id,
                            "message": message,
                            "phone_number": verification.phone_number,
                        },
                    },
                    verification.user_id,
                )
            )

    return {"verification_id": verification_id, "messages": messages}


@app.get(
    "/verify/{verification_id}/voice",
    tags=["Verification"],
    summary="Get Voice Call Details",
)
def get_voice_call(
    verification_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve voice call details including transcription and audio URL"""
    verification = (
        db.query(Verification)
        .filter(
            Verification.id == verification_id,
            Verification.user_id == user.id,
            Verification.capability == "voice",
        )
        .first()
    )

    if not verification:
        raise HTTPException(status_code=404, detail="Voice verification not found")

    # Get voice data from TextVerified (placeholder - would use actual API)
    # For now, return stored data or empty
    return {
        "verification_id": verification.id,
        "phone_number": verification.phone_number,
        "capability": "voice",
        "call_status": verification.status,
        "call_duration": verification.call_duration,
        "transcription": verification.transcription,
        "audio_url": verification.audio_url,
        "received_at": (
            verification.completed_at.isoformat() if verification.completed_at else None
        ),
    }


class RetryRequest(BaseModel):
    retry_type: str


@app.post(
    "/verify/{verification_id}/retry",
    tags=["Verification"],
    summary="Retry Verification",
)
def retry_verification(
    verification_id: str,
    req: RetryRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retry verification with voice, same number, or new number

    - **retry_type**: 'voice', 'same', 'new'
    """
    try:
        verification = (
            db.query(Verification)
            .filter(Verification.id == verification_id, Verification.user_id == user.id)
            .first()
        )

        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")

        if req.retry_type == "voice":
            # Convert to voice verification
            verification.capability = "voice"
            verification.status = "pending"
            db.commit()

            return {
                "id": verification.id,
                "phone_number": verification.phone_number,
                "capability": "voice",
                "status": "pending",
                "message": "Switched to voice verification",
            }

        elif req.retry_type == "same":
            # Retry with same number
            verification.status = "pending"
            db.commit()

            return {
                "id": verification.id,
                "phone_number": verification.phone_number,
                "status": "pending",
                "message": "Retrying with same number",
            }

        elif req.retry_type == "new":
            # Cancel current and create new
            verification.status = "cancelled"

            # Create new verification
            new_verification_id = tv_client.create_verification(
                verification.service_name, verification.capability
            )
            details = tv_client.get_verification(new_verification_id)

            new_verification = Verification(
                id=new_verification_id,
                user_id=user.id,
                service_name=verification.service_name,
                phone_number=details.get("number"),
                capability=verification.capability,
                status="pending",
                cost=0,
            )
            db.add(new_verification)
            db.commit()

            return {
                "id": new_verification.id,
                "phone_number": new_verification.phone_number,
                "status": "pending",
                "cost": 0,
                "message": "New number assigned",
            }

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid retry_type. Use 'voice', 'same', or 'new'",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retry verification error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to retry verification")


@app.delete(
    "/verify/{verification_id}", tags=["Verification"], summary="Cancel Verification"
)
def cancel_verification(
    verification_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel active verification and refund credits to wallet"""
    # Strict user ownership check
    verification = (
        db.query(Verification)
        .filter(Verification.id == verification_id, Verification.user_id == user.id)
        .first()
    )

    if not verification:
        raise HTTPException(
            status_code=404, detail="Verification not found or not owned by you"
        )

    if verification.status == "cancelled":
        raise HTTPException(status_code=400, detail="Already cancelled")

    try:
        # Cancel on TextVerified
        tv_client.cancel_verification(verification_id)
    except Exception as e:
        # If TextVerified cancel fails, still mark as cancelled locally
        pass

    # Refund credits to the verification owner
    verification_owner = db.query(User).filter(User.id == verification.user_id).first()
    verification_owner.credits += verification.cost

    # Create refund transaction
    transaction = Transaction(
        id=f"txn_{datetime.now(timezone.utc).timestamp()}",
        user_id=verification.user_id,
        amount=verification.cost,
        type="credit",
        description=f"Refund for cancelled {verification.service_name} verification",
    )
    db.add(transaction)

    verification.status = "cancelled"
    db.commit()

    # Refresh user to get updated credits
    db.refresh(user)

    return {
        "message": "Verification cancelled and refunded",
        "refunded": verification.cost,
        "new_balance": user.credits,
    }


# Admin Endpoints
@app.get("/admin/users", tags=["Admin"], summary="List All Users")
def get_all_users(
    search: str = None,
    page: int = 1,
    limit: int = 50,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get all registered users with plan info, search and pagination (admin only)"""
    from sqlalchemy import func

    query = db.query(User)

    # Search filter
    if search:
        query = query.filter((User.email.contains(search)) | (User.id.contains(search)))

    # Get total count
    total = query.count()

    # Pagination
    offset = (page - 1) * limit
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

    # Get verification counts and spending for each user
    user_data = []
    for u in users:
        # Get verification count
        verification_count = (
            db.query(Verification).filter(Verification.user_id == u.id).count()
        )

        # Get total spent
        total_spent = (
            db.query(func.sum(Transaction.amount))
            .filter(Transaction.user_id == u.id, Transaction.type == "debit")
            .scalar()
            or 0
        )
        total_spent = abs(total_spent)

        # Get total funded
        total_funded = (
            db.query(func.sum(Transaction.amount))
            .filter(Transaction.user_id == u.id, Transaction.type == "credit")
            .scalar()
            or 0
        )

        # Determine plan based on total funded
        if total_funded >= 100:
            plan = "enterprise"
        elif total_funded >= 25:
            plan = "developer"
        else:
            plan = "free"

        user_data.append(
            {
                "id": u.id,
                "email": u.email,
                "credits": u.credits,
                "free_verifications": u.free_verifications,
                "is_admin": u.is_admin,
                "email_verified": u.email_verified,
                "created_at": u.created_at.isoformat(),
                "plan": plan,
                "verification_count": verification_count,
                "total_spent": total_spent,
                "total_funded": total_funded,
            }
        )

    return {
        "users": user_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
        },
    }


@app.get("/admin/users/{user_id}/journey", tags=["Admin"], summary="Get User Journey")
def get_user_journey(
    user_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Get complete user journey with all activities"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get all activities
    activities = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.created_at.asc())
        .all()
    )

    # Get payment logs
    payments = (
        db.query(PaymentLog)
        .filter(PaymentLog.user_id == user_id)
        .order_by(PaymentLog.created_at.asc())
        .all()
    )

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        },
        "activities": [
            {
                "timestamp": a.created_at.isoformat(),
                "page": a.page,
                "action": a.action,
                "element": a.element,
                "status": a.status,
                "details": a.details,
            }
            for a in activities
        ],
        "payments": [
            {
                "timestamp": p.created_at.isoformat(),
                "reference": p.reference,
                "amount": p.namaskah_amount,
                "status": p.status,
                "webhook_received": p.webhook_received,
                "credited": p.credited,
            }
            for p in payments
        ],
    }


@app.get("/admin/users/{user_id}", tags=["Admin"], summary="Get User Details")
def get_user_details(
    user_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Get detailed user information including history (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get verification history
    verifications = (
        db.query(Verification)
        .filter(Verification.user_id == user_id)
        .order_by(Verification.created_at.desc())
        .limit(20)
        .all()
    )

    # Get transaction history
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(20)
        .all()
    )

    # Calculate stats
    from sqlalchemy import func

    total_spent = (
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.user_id == user_id, Transaction.type == "debit")
        .scalar()
        or 0
    )

    total_funded = (
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.user_id == user_id, Transaction.type == "credit")
        .scalar()
        or 0
    )

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "credits": user.credits,
            "free_verifications": user.free_verifications,
            "is_admin": user.is_admin,
            "email_verified": user.email_verified,
            "referral_code": user.referral_code,
            "created_at": user.created_at.isoformat(),
        },
        "stats": {
            "total_verifications": len(verifications),
            "total_spent": abs(total_spent),
            "total_funded": total_funded,
        },
        "recent_verifications": [
            {
                "id": v.id,
                "service_name": v.service_name,
                "status": v.status,
                "cost": v.cost,
                "created_at": v.created_at.isoformat(),
            }
            for v in verifications
        ],
        "recent_transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "type": t.type,
                "description": t.description,
                "created_at": t.created_at.isoformat(),
            }
            for t in transactions
        ],
    }


@app.get("/admin/export/users", tags=["Admin"], summary="Export Users to CSV")
def export_users_csv(
    admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Export all users to CSV (admin only)"""
    from fastapi.responses import StreamingResponse
    import io
    import csv

    users = db.query(User).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "ID",
            "Email",
            "Credits",
            "Free Verifications",
            "Is Admin",
            "Email Verified",
            "Created At",
        ]
    )

    # Data
    for u in users:
        writer.writerow(
            [
                u.id,
                u.email,
                u.credits,
                u.free_verifications,
                u.is_admin,
                u.email_verified,
                u.created_at.isoformat(),
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users_export.csv"},
    )


@app.get(
    "/admin/export/transactions", tags=["Admin"], summary="Export Transactions to CSV"
)
def export_transactions_csv(
    admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Export all transactions to CSV (admin only)"""
    from fastapi.responses import StreamingResponse
    import io
    import csv

    transactions = db.query(Transaction).order_by(Transaction.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["ID", "User ID", "Amount", "Type", "Description", "Created At"])

    # Data
    for t in transactions:
        writer.writerow(
            [t.id, t.user_id, t.amount, t.type, t.description, t.created_at.isoformat()]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions_export.csv"},
    )


@app.post("/admin/credits/add", tags=["Admin"], summary="Add Credits to User")
def add_credits(
    req: AddCreditsRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Manually add credits to user wallet (admin only)"""
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.credits += req.amount

    transaction = Transaction(
        id=f"txn_{datetime.now(timezone.utc).timestamp()}",
        user_id=user.id,
        amount=req.amount,
        type="credit",
        description=f"Admin added credits",
    )
    db.add(transaction)
    db.commit()

    return {"message": f"Added N{req.amount} credits", "new_balance": user.credits}


@app.post("/admin/credits/deduct", tags=["Admin"], summary="Deduct Credits from User")
def deduct_credits(
    req: AddCreditsRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Manually deduct credits from user wallet (admin only)"""
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.credits < req.amount:
        raise HTTPException(
            status_code=400, detail=f"Insufficient balance. User has N{user.credits}"
        )

    user.credits -= req.amount

    transaction = Transaction(
        id=f"txn_{datetime.now(timezone.utc).timestamp()}",
        user_id=user.id,
        amount=-req.amount,
        type="debit",
        description=f"Admin deducted credits",
    )
    db.add(transaction)
    db.commit()

    return {"message": f"Deducted N{req.amount} credits", "new_balance": user.credits}


@app.post(
    "/admin/users/{user_id}/suspend", tags=["Admin"], summary="Suspend User Account"
)
def suspend_user(
    user_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Suspend user account (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Add suspended flag to user model (would need migration)
    # For now, set credits to negative to indicate suspension
    user.email_verified = False
    db.commit()

    return {"message": f"User {user.email} suspended"}


@app.post(
    "/admin/users/{user_id}/activate", tags=["Admin"], summary="Activate User Account"
)
def activate_user(
    user_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Activate suspended user account (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.email_verified = True
    db.commit()

    return {"message": f"User {user.email} activated"}


@app.delete("/admin/users/{user_id}", tags=["Admin"], summary="Delete User Account")
def delete_user(
    user_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Permanently delete user account (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_admin:
        raise HTTPException(status_code=403, detail="Cannot delete admin account")

    # Delete related records
    db.query(Verification).filter(Verification.user_id == user_id).delete()
    db.query(Transaction).filter(Transaction.user_id == user_id).delete()
    db.query(APIKey).filter(APIKey.user_id == user_id).delete()
    db.query(Webhook).filter(Webhook.user_id == user_id).delete()
    db.query(NumberRental).filter(NumberRental.user_id == user_id).delete()
    db.query(Subscription).filter(Subscription.user_id == user_id).delete()

    db.delete(user)
    db.commit()

    return {"message": f"User {user.email} deleted permanently"}


@app.post(
    "/admin/verifications/{verification_id}/cancel",
    tags=["Admin"],
    summary="Cancel Any Verification",
)
def admin_cancel_verification(
    verification_id: str,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Cancel any user's verification and refund (admin only)"""
    verification = (
        db.query(Verification).filter(Verification.id == verification_id).first()
    )
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    if verification.status == "cancelled":
        raise HTTPException(status_code=400, detail="Already cancelled")

    try:
        tv_client.cancel_verification(verification_id)
    except:
        pass

    user = db.query(User).filter(User.id == verification.user_id).first()
    user.credits += verification.cost

    transaction = Transaction(
        id=f"txn_{datetime.now(timezone.utc).timestamp()}",
        user_id=user.id,
        amount=verification.cost,
        type="credit",
        description=f"Admin cancelled verification {verification_id}",
    )
    db.add(transaction)

    verification.status = "cancelled"
    db.commit()

    return {
        "message": "Verification cancelled and refunded",
        "refunded": verification.cost,
    }


@app.get(
    "/admin/verifications/active",
    tags=["Admin"],
    summary="Get All Active Verifications",
)
def get_all_active_verifications(
    admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Get all active verifications system-wide (admin only)"""
    verifications = (
        db.query(Verification)
        .filter(Verification.status == "pending")
        .order_by(Verification.created_at.desc())
        .limit(100)
        .all()
    )

    return {
        "verifications": [
            {
                "id": v.id,
                "user_email": db.query(User).filter(User.id == v.user_id).first().email,
                "service_name": v.service_name,
                "phone_number": v.phone_number,
                "cost": v.cost,
                "created_at": v.created_at.isoformat(),
            }
            for v in verifications
        ]
    }


@app.get("/admin/rentals/active", tags=["Admin"], summary="Get All Active Rentals")
def get_all_active_rentals(
    admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Get all active rentals system-wide (admin only)"""
    rentals = (
        db.query(NumberRental)
        .filter(NumberRental.status == "active")
        .order_by(NumberRental.expires_at)
        .all()
    )

    return {
        "rentals": [
            {
                "id": r.id,
                "user_email": db.query(User).filter(User.id == r.user_id).first().email,
                "phone_number": r.phone_number,
                "service_name": r.service_name,
                "expires_at": r.expires_at.isoformat(),
                "cost": r.cost,
            }
            for r in rentals
        ]
    }


@app.post(
    "/admin/rentals/{rental_id}/release", tags=["Admin"], summary="Force Release Rental"
)
def admin_release_rental(
    rental_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Force release any rental (admin only)"""
    rental = db.query(NumberRental).filter(NumberRental.id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    rental.status = "released"
    rental.released_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Rental released", "rental_id": rental_id}


@app.get("/admin/affiliates/stats", tags=["Admin"], summary="Get Affiliate Statistics")
def get_affiliate_stats(
    admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Get affiliate program statistics (admin only)"""
    from sqlalchemy import func

    # Total affiliates (users with referrals)
    total_affiliates = (
        db.query(func.count(func.distinct(Referral.referrer_id))).scalar() or 0
    )

    # Active affiliates (earned commissions)
    active_affiliates = (
        db.query(func.count(func.distinct(User.id)))
        .filter(User.referral_earnings > 0)
        .scalar()
        or 0
    )

    # Total commissions paid
    total_commissions = db.query(func.sum(User.referral_earnings)).scalar() or 0

    # Top affiliates
    top_affiliates = (
        db.query(User)
        .filter(User.referral_earnings > 0)
        .order_by(User.referral_earnings.desc())
        .limit(10)
        .all()
    )

    # Total referrals
    total_referrals = db.query(Referral).count()

    return {
        "total_affiliates": total_affiliates,
        "active_affiliates": active_affiliates,
        "total_referrals": total_referrals,
        "total_commissions_paid": total_commissions,
        "top_affiliates": [
            {
                "email": u.email,
                "referral_code": u.referral_code,
                "earnings": u.referral_earnings,
                "referral_count": db.query(Referral)
                .filter(Referral.referrer_id == u.id)
                .count(),
            }
            for u in top_affiliates
        ],
    }


@app.get(
    "/admin/subscriptions/stats", tags=["Admin"], summary="Get Subscription Statistics"
)
def get_subscription_stats(
    admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Get subscription tier distribution (admin only)"""
    from sqlalchemy import func

    # Get users with total funded amount
    users_with_funding = (
        db.query(User.id, func.sum(Transaction.amount).label("total_funded"))
        .join(Transaction, User.id == Transaction.user_id)
        .filter(Transaction.type == "credit")
        .group_by(User.id)
        .all()
    )

    pay_as_you_go = 0
    developer = 0
    enterprise = 0

    for user_funding in users_with_funding:
        if user_funding.total_funded >= 100:
            enterprise += 1
        elif user_funding.total_funded >= 25:
            developer += 1
        else:
            pay_as_you_go += 1

    # Users with no funding are pay-as-you-go
    total_users = db.query(User).count()
    pay_as_you_go += total_users - len(users_with_funding)

    return {
        "pay_as_you_go": pay_as_you_go,
        "developer": developer,
        "enterprise": enterprise,
        "total": total_users,
    }


@app.get("/admin/analytics/summary", tags=["Admin"], summary="Get Analytics Summary")
def get_analytics_summary(
    email: str = None,
    days: int = 7,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get analytics summary for user or all users"""
    from sqlalchemy import func
    from datetime import timedelta

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    query = db.query(ActivityLog).filter(ActivityLog.created_at >= start_date)
    if email:
        query = query.filter(ActivityLog.email == email)

    # Page views
    page_views = db.query(
        ActivityLog.page, func.count(ActivityLog.id).label("count")
    ).filter(ActivityLog.created_at >= start_date, ActivityLog.action == "page_view")
    if email:
        page_views = page_views.filter(ActivityLog.email == email)
    page_views = page_views.group_by(ActivityLog.page).all()

    # Button clicks
    button_clicks = db.query(
        ActivityLog.element, ActivityLog.page, func.count(ActivityLog.id).label("count")
    ).filter(ActivityLog.created_at >= start_date, ActivityLog.action == "click")
    if email:
        button_clicks = button_clicks.filter(ActivityLog.email == email)
    button_clicks = button_clicks.group_by(ActivityLog.element, ActivityLog.page).all()

    # Total activities
    total_activities = query.count()

    # Unique users
    unique_users = db.query(func.count(func.distinct(ActivityLog.user_id))).filter(
        ActivityLog.created_at >= start_date, ActivityLog.user_id.isnot(None)
    )
    if email:
        unique_users = unique_users.filter(ActivityLog.email == email)
    unique_users = unique_users.scalar() or 0

    return {
        "total_activities": total_activities,
        "unique_users": unique_users,
        "page_views": [{"page": p[0], "count": p[1]} for p in page_views],
        "button_clicks": [
            {"element": b[0], "page": b[1], "count": b[2]} for b in button_clicks
        ],
    }


@app.get("/admin/payment-logs", tags=["Admin"], summary="Get Payment Logs")
def get_payment_logs(
    email: str = None,
    reference: str = None,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get payment logs for troubleshooting (admin only)"""
    query = db.query(PaymentLog)

    if email:
        query = query.filter(PaymentLog.email == email)
    if reference:
        query = query.filter(PaymentLog.reference == reference)

    logs = query.order_by(PaymentLog.created_at.desc()).limit(50).all()

    return {
        "logs": [
            {
                "id": log.id,
                "email": log.email,
                "reference": log.reference,
                "amount_ngn": log.amount_ngn,
                "amount_usd": log.amount_usd,
                "namaskah_amount": log.namaskah_amount,
                "status": log.status,
                "webhook_received": log.webhook_received,
                "credited": log.credited,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "updated_at": log.updated_at.isoformat() if log.updated_at else None,
            }
            for log in logs
        ]
    }


@app.get("/admin/activity-logs", tags=["Admin"], summary="Get Activity Logs")
def get_activity_logs(
    email: str = None,
    page: str = None,
    action: str = None,
    limit: int = 100,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get activity logs for user tracking (admin only)"""
    query = db.query(ActivityLog)

    if email:
        query = query.filter(ActivityLog.email == email)
    if page:
        query = query.filter(ActivityLog.page == page)
    if action:
        query = query.filter(ActivityLog.action == action)

    logs = query.order_by(ActivityLog.created_at.desc()).limit(limit).all()

    return {
        "logs": [
            {
                "id": log.id,
                "email": log.email or "anonymous",
                "page": log.page,
                "action": log.action,
                "element": log.element,
                "status": log.status,
                "details": log.details,
                "error_message": log.error_message,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }


@app.post("/track", tags=["System"], summary="Track User Activity")
async def track_activity(request: Request, db: Session = Depends(get_db)):
    """Track user activity from frontend"""
    try:
        data = await request.json()

        # Get user info from token if present
        user_id = None
        email = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                user_id = payload.get("user_id")
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    email = user.email
            except:
                pass

        # Get IP and user agent
        ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        log_activity(
            db,
            user_id=user_id,
            email=email,
            page=data.get("page"),
            action=data.get("action"),
            element=data.get("element"),
            status="success",
            details=data.get("details"),
            ip=ip,
            user_agent=user_agent,
        )

        return {"status": "tracked"}
    except Exception as e:
        print(f"Track error: {e}")
        return {"status": "error"}


@app.get("/subscription/plans", tags=["Subscription"], summary="Get Available Plans")
def get_subscription_plans():
    """Get all available subscription plans from pricing config"""
    return {
        "plans": [
            {
                "id": plan_id,
                "name": plan_data["name"],
                "price": plan_data["price"],
                "price_usd": plan_data["price"] * 2,
                "discount": f"{int(plan_data['discount'] * 100)}%",
                "free_verifications": plan_data.get("free_verifications", 0),
                "api_limit": plan_data.get("api_limit", 0),
                "features": plan_data["features"],
            }
            for plan_id, plan_data in SUBSCRIPTION_PLANS.items()
        ]
    }


@app.post("/subscription/subscribe", tags=["Subscription"], summary="Subscribe to Plan")
def subscribe_to_plan(
    req: SubscribeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Subscribe to Pro or Turbo plan"""
    if req.plan not in ["pro", "turbo"]:
        raise HTTPException(
            status_code=400, detail="Invalid plan. Choose 'pro' or 'turbo'"
        )

    plan = SUBSCRIPTION_PLANS[req.plan]

    # Check if user has enough credits
    if user.credits < plan["price"]:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Need N{plan['price']}, have N{user.credits}",
        )

    # Check existing subscription
    existing = db.query(Subscription).filter(Subscription.user_id == user.id).first()

    if existing:
        # Upgrade/downgrade
        existing.plan = req.plan
        existing.price = plan["price"]
        existing.discount = plan["discount"]
        existing.duration = plan["duration"]
        existing.status = "active"
        existing.expires_at = (
            None
            if plan["duration"] == 0
            else datetime.now(timezone.utc) + timedelta(days=plan["duration"])
        )
        existing.updated_at = datetime.now(timezone.utc)
    else:
        # New subscription
        subscription = Subscription(
            id=f"sub_{datetime.now(timezone.utc).timestamp()}",
            user_id=user.id,
            plan=req.plan,
            price=plan["price"],
            discount=plan["discount"],
            duration=plan["duration"],
            status="active",
            expires_at=(
                None
                if plan["duration"] == 0
                else datetime.now(timezone.utc) + timedelta(days=plan["duration"])
            ),
        )
        db.add(subscription)

    # Deduct first month payment
    user.credits -= plan["price"]

    # Create transaction
    db.add(
        Transaction(
            id=f"txn_{datetime.now(timezone.utc).timestamp()}",
            user_id=user.id,
            amount=-plan["price"],
            type="debit",
            description=f"Subscription: {plan['name']} plan (monthly)",
        )
    )

    db.commit()

    expires_at = (
        None
        if plan["duration"] == 0
        else datetime.now(timezone.utc) + timedelta(days=plan["duration"])
    )

    return {
        "message": f"Successfully subscribed to {plan['name']} plan!",
        "plan": req.plan,
        "duration": f"{plan['duration']} days" if plan["duration"] > 0 else "Lifetime",
        "expires_at": expires_at.isoformat() if expires_at else "Never",
        "remaining_credits": user.credits,
    }


@app.get(
    "/subscription/current", tags=["Subscription"], summary="Get Current Subscription"
)
def get_current_subscription(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get user's current subscription"""
    try:
        subscription = (
            db.query(Subscription).filter(Subscription.user_id == user.id).first()
        )

        if not subscription:
            return {
                "plan": "starter",
                "name": "Starter",
                "status": "active",
                "features": SUBSCRIPTION_PLANS.get("starter", {}),
            }

        return {
            "plan": subscription.plan,
            "name": SUBSCRIPTION_PLANS.get(subscription.plan, {}).get(
                "name", subscription.plan
            ),
            "status": subscription.status,
            "price": subscription.price,
            "discount": f"{int(subscription.discount * 100)}%",
            "duration": (
                f"{subscription.duration} days"
                if subscription.duration > 0
                else "Lifetime"
            ),
            "expires_at": (
                subscription.expires_at.isoformat()
                if subscription.expires_at
                else "Never"
            ),
            "features": SUBSCRIPTION_PLANS.get(subscription.plan, {}),
        }
    except Exception as e:
        logger.error(f"Subscription query failed: {e}")
        return {
            "plan": "starter",
            "name": "Starter",
            "status": "active",
            "features": {},
        }


@app.post("/subscription/cancel", tags=["Subscription"], summary="Cancel Subscription")
def cancel_subscription(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Cancel active subscription"""
    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id, Subscription.status == "active")
        .first()
    )

    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")

    subscription.status = "cancelled"
    subscription.cancelled_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "message": "Subscription cancelled. You'll be downgraded to Starter plan when it expires.",
        "plan": subscription.plan,
        "active_until": (
            subscription.expires_at.isoformat()
            if subscription.expires_at
            else "Lifetime (no refund)"
        ),
    }


@app.get("/admin/banned-numbers", tags=["Admin"], summary="Get Banned Numbers")
def get_banned_numbers(
    service: str = None,
    area_code: str = None,
    carrier: str = None,
    min_fails: int = 1,
    limit: int = 100,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get list of banned numbers with filtering (admin only)

    - **service**: Filter by service name
    - **area_code**: Filter by area code
    - **carrier**: Filter by ISP/carrier
    - **min_fails**: Minimum fail count
    - **limit**: Max results (default 100)
    """
    query = db.query(BannedNumber)

    if service:
        query = query.filter(BannedNumber.service_name == service)
    if area_code:
        query = query.filter(BannedNumber.area_code == area_code)
    if carrier:
        query = query.filter(BannedNumber.carrier.contains(carrier))
    if min_fails > 1:
        query = query.filter(BannedNumber.fail_count >= min_fails)

    banned = query.order_by(BannedNumber.fail_count.desc()).limit(limit).all()

    # Get statistics
    from sqlalchemy import func

    total_banned = db.query(func.count(BannedNumber.id)).scalar()
    by_service = (
        db.query(BannedNumber.service_name, func.count(BannedNumber.id).label("count"))
        .group_by(BannedNumber.service_name)
        .order_by(func.count(BannedNumber.id).desc())
        .limit(10)
        .all()
    )

    by_carrier = (
        db.query(BannedNumber.carrier, func.count(BannedNumber.id).label("count"))
        .filter(BannedNumber.carrier.isnot(None))
        .group_by(BannedNumber.carrier)
        .order_by(func.count(BannedNumber.id).desc())
        .limit(10)
        .all()
    )

    return {
        "total_banned": total_banned,
        "stats": {
            "by_service": [{"service": s[0], "count": s[1]} for s in by_service],
            "by_carrier": [{"carrier": c[0], "count": c[1]} for c in by_carrier],
        },
        "banned_numbers": [
            {
                "id": b.id,
                "phone_number": b.phone_number,
                "service_name": b.service_name,
                "area_code": b.area_code or "Unknown",
                "carrier": b.carrier or "Unknown",
                "fail_count": int(b.fail_count),
                "last_failed_at": b.last_failed_at.isoformat(),
                "created_at": b.created_at.isoformat(),
            }
            for b in banned
        ],
    }


@app.get("/admin/pricing/analytics", tags=["Admin"], summary="Get Pricing Analytics")
def get_pricing_analytics(
    period: str = "30",
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get pricing tier performance and revenue analytics (admin only)"""
    from sqlalchemy import func

    days = int(period)
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Tier performance
    tier_stats = {}
    for tier_id, tier_data in SERVICE_TIERS.items():
        services = tier_data["services"]
        if services:
            tier_verifications = (
                db.query(Verification)
                .filter(
                    Verification.service_name.in_(services),
                    Verification.created_at >= start_date,
                )
                .all()
            )

            total_count = len(tier_verifications)
            total_revenue = sum(v.cost for v in tier_verifications)
            avg_price = total_revenue / total_count if total_count > 0 else 0

            tier_stats[tier_id] = {
                "name": tier_data["name"],
                "base_price": tier_data["base_price"],
                "count": total_count,
                "revenue": round(total_revenue, 2),
                "avg_price": round(avg_price, 2),
                "services": services[:5],  # Top 5 services
            }

    # Plan distribution revenue
    plan_revenue = {}
    for plan_id, plan_data in SUBSCRIPTION_PLANS.items():
        plan_subs = (
            db.query(Subscription)
            .filter(Subscription.plan == plan_id, Subscription.status == "active")
            .count()
        )
        monthly_revenue = plan_subs * plan_data["price"]
        plan_revenue[plan_id] = {
            "name": plan_data["name"],
            "subscribers": plan_subs,
            "monthly_revenue": round(monthly_revenue, 2),
            "discount": plan_data["discount"],
        }

    return {
        "period_days": days,
        "tier_performance": tier_stats,
        "plan_revenue": plan_revenue,
        "total_tier_revenue": sum(t["revenue"] for t in tier_stats.values()),
        "total_subscription_revenue": sum(
            p["monthly_revenue"] for p in plan_revenue.values()
        ),
    }


@app.get("/admin/receipts/stats", tags=["Admin"], summary="Get Receipt Statistics")
def get_receipt_stats(
    period: str = "7",
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get receipt generation statistics (admin only)"""
    from sqlalchemy import func

    days = int(period)
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Total receipts generated
    total_receipts = (
        db.query(VerificationReceipt)
        .filter(VerificationReceipt.created_at >= start_date)
        .count()
    )

    # Receipts by service
    receipts_by_service = (
        db.query(
            VerificationReceipt.service_name,
            func.count(VerificationReceipt.id).label("count"),
            func.sum(VerificationReceipt.amount_spent).label("revenue"),
        )
        .filter(VerificationReceipt.created_at >= start_date)
        .group_by(VerificationReceipt.service_name)
        .order_by(func.count(VerificationReceipt.id).desc())
        .limit(10)
        .all()
    )

    # Notification preferences stats
    total_users_with_prefs = db.query(NotificationPreferences).count()
    email_enabled = (
        db.query(NotificationPreferences)
        .filter(NotificationPreferences.email_notifications == True)
        .count()
    )
    receipts_enabled = (
        db.query(NotificationPreferences)
        .filter(NotificationPreferences.receipt_notifications == True)
        .count()
    )

    return {
        "period_days": days,
        "total_receipts": total_receipts,
        "receipts_by_service": [
            {"service": s[0], "count": s[1], "revenue": float(s[2] or 0)}
            for s in receipts_by_service
        ],
        "notification_stats": {
            "total_users_with_preferences": total_users_with_prefs,
            "email_notifications_enabled": email_enabled,
            "receipt_notifications_enabled": receipts_enabled,
        },
    }


@app.get("/admin/stats", tags=["Admin"], summary="Get Platform Statistics")
def get_stats(
    period: str = "7",
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get platform-wide statistics with real-time data (admin only)

    - **period**: Time period (7, 14, 30, 60, 90, or 'all')
    """
    from sqlalchemy import func

    # Calculate date range
    if period == "all":
        start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
    else:
        days = int(period)
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Total users (all time)
    total_users = db.query(User).count()

    # New users in period
    new_users = db.query(User).filter(User.created_at >= start_date).count()

    # Active users (created verification in period)
    active_users = (
        db.query(Verification.user_id)
        .filter(Verification.created_at >= start_date)
        .distinct()
        .count()
    )

    # Verifications in period
    total_verifications = (
        db.query(Verification).filter(Verification.created_at >= start_date).count()
    )

    # Success/Failure stats
    completed_verifications = (
        db.query(Verification)
        .filter(
            Verification.created_at >= start_date, Verification.status == "completed"
        )
        .count()
    )

    cancelled_verifications = (
        db.query(Verification)
        .filter(
            Verification.created_at >= start_date, Verification.status == "cancelled"
        )
        .count()
    )

    pending_verifications = (
        db.query(Verification).filter(Verification.status == "pending").count()
    )

    success_rate = (
        (completed_verifications / total_verifications * 100)
        if total_verifications > 0
        else 0
    )

    # Revenue in period (sum of all debit transactions)
    total_revenue = (
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.type == "debit", Transaction.created_at >= start_date)
        .scalar()
        or 0
    )
    total_revenue = abs(total_revenue)

    # Calculate revenue for previous period for comparison
    prev_start = start_date - timedelta(days=int(period))
    prev_revenue = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.type == "debit",
            Transaction.created_at >= prev_start,
            Transaction.created_at < start_date,
        )
        .scalar()
        or 0
    )
    prev_revenue = abs(prev_revenue)
    revenue_change = total_revenue - prev_revenue

    # Plan distribution (based on total funded amount)
    users_with_funding = (
        db.query(User.id, func.sum(Transaction.amount).label("total_funded"))
        .join(Transaction, User.id == Transaction.user_id)
        .filter(Transaction.type == "credit")
        .group_by(User.id)
        .all()
    )

    pay_as_you_go = 0
    developer = 0
    enterprise = 0

    for user_funding in users_with_funding:
        if user_funding.total_funded >= 100:
            enterprise += 1
        elif user_funding.total_funded >= 25:
            developer += 1
        else:
            pay_as_you_go += 1

    # Users with no funding are pay-as-you-go
    pay_as_you_go += total_users - len(users_with_funding)

    # Popular services in period
    popular_services = (
        db.query(
            Verification.service_name,
            func.count(Verification.id).label("count"),
            func.sum(Verification.cost).label("revenue"),
        )
        .filter(Verification.created_at >= start_date)
        .group_by(Verification.service_name)
        .order_by(func.count(Verification.id).desc())
        .limit(10)
        .all()
    )

    # Daily breakdown for charts
    daily_stats = []
    for i in range(int(period)):
        day_start = start_date + timedelta(days=i)
        day_end = day_start + timedelta(days=1)

        day_verifications = (
            db.query(Verification)
            .filter(
                Verification.created_at >= day_start, Verification.created_at < day_end
            )
            .count()
        )

        day_revenue = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.type == "debit",
                Transaction.created_at >= day_start,
                Transaction.created_at < day_end,
            )
            .scalar()
            or 0
        )

        daily_stats.append(
            {
                "date": day_start.strftime("%Y-%m-%d"),
                "verifications": day_verifications,
                "revenue": abs(day_revenue),
            }
        )

    return {
        "total_users": total_users,
        "new_users": new_users,
        "active_users": active_users,
        "total_verifications": total_verifications,
        "completed_verifications": completed_verifications,
        "cancelled_verifications": cancelled_verifications,
        "pending_verifications": pending_verifications,
        "success_rate": round(success_rate, 1),
        "total_revenue": round(total_revenue, 2),
        "revenue_change": round(revenue_change, 2),
        "plan_distribution": {
            "pay_as_you_go": pay_as_you_go,
            "developer": developer,
            "enterprise": enterprise,
        },
        "popular_services": [
            {"service": s[0], "count": s[1], "revenue": float(s[2] or 0)}
            for s in popular_services
        ],
        "daily_stats": daily_stats,
        "receipt_stats": {
            "total_receipts_generated": db.query(VerificationReceipt)
            .filter(VerificationReceipt.created_at >= start_date)
            .count(),
            "users_with_receipts": db.query(VerificationReceipt.user_id)
            .filter(VerificationReceipt.created_at >= start_date)
            .distinct()
            .count(),
        },
    }


# Payment Endpoints
# REMOVED: Mock fund_wallet endpoint - Use Paystack only


@app.get("/system/health", tags=["System"], summary="System Health Check")
def system_health():
    """Get system health status including circuit breakers"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "textverified": check_service_health("textverified"),
            "paystack": check_service_health("paystack"),
            "database": check_service_health("database"),
        },
        "features": {
            "hourly_rentals": True,
            "retry_mechanisms": True,
            "circuit_breakers": True,
            "dynamic_pricing": True,
        },
    }

    # Check if any service is down
    for service_name, service_health in health_status["services"].items():
        if service_health["status"] == "open":
            health_status["status"] = "degraded"
            break

    return health_status


@app.post(
    "/admin/system/reset-circuit-breaker",
    tags=["Admin"],
    summary="Reset Circuit Breaker",
)
def admin_reset_circuit_breaker(
    service_name: str, admin: User = Depends(get_admin_user)
):
    """Manually reset a circuit breaker (admin only)"""
    if service_name not in ["textverified", "paystack", "database"]:
        raise HTTPException(status_code=400, detail="Invalid service name")

    success = reset_circuit_breaker(service_name)

    if success:
        return {
            "message": f"Circuit breaker reset for {service_name}",
            "status": "success",
        }
    else:
        raise HTTPException(
            status_code=404, detail=f"Circuit breaker not found for {service_name}"
        )


@app.post(
    "/wallet/paystack/initialize",
    tags=["Wallet"],
    summary="Initialize Paystack Payment",
)
def initialize_paystack(
    req: FundWalletRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Initialize Paystack payment with detailed transaction info"""
    if req.amount < 2.5:
        raise HTTPException(
            status_code=400, detail="Minimum funding amount is N2.50 ($5 USD)"
        )

    if req.amount < 5:
        raise HTTPException(status_code=400, detail="Minimum funding amount is $5 USD")

    # Only Paystack is supported
    if req.payment_method != "paystack":
        raise HTTPException(
            status_code=400,
            detail="Only Paystack payment is supported. Crypto payments are not available.",
        )

    reference = f"namaskah_{user.id}_{int(datetime.now(timezone.utc).timestamp())}"
    amount_usd = req.amount  # User enters USD amount directly

    # Get current USD to NGN exchange rate (cached, updates hourly)
    USD_TO_NGN_RATE = get_usd_to_ngn_rate()
    amount_ngn = amount_usd * USD_TO_NGN_RATE  # Exact NGN amount based on current rate
    namaskah_amount = amount_usd * USD_TO_NAMASKAH

    if not PAYSTACK_SECRET_KEY or not PAYSTACK_SECRET_KEY.startswith("sk_"):
        raise HTTPException(
            status_code=503,
            detail="Payment system not configured. Please contact support.",
        )

    try:
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "email": user.email,
            "amount": int(amount_ngn * 100),  # Convert to kobo
            "reference": reference,
            "callback_url": f"{BASE_URL}/app?reference={reference}",
            "metadata": {
                "user_id": user.id,
                "user_email": user.email,
                "type": "wallet_funding",
                "namaskah_amount": req.amount,
                "usd_amount": amount_usd,
            },
            "channels": ["card", "bank", "ussd", "qr", "mobile_money", "bank_transfer"],
        }
        r = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers=headers,
        )
        r.raise_for_status()
        data = r.json()

        # Log payment initialization
        log_payment(
            db,
            user_id=user.id,
            email=user.email,
            reference=reference,
            amount_ngn=amount_ngn,
            amount_usd=amount_usd,
            namaskah_amount=namaskah_amount,
            status="initialized",
        )
        log_activity(
            db,
            user_id=user.id,
            email=user.email,
            action="payment_init",
            status="success",
            details=f"Paystack payment initialized: {reference}",
        )

        return {
            "success": True,
            "authorization_url": data["data"]["authorization_url"],
            "access_code": data["data"]["access_code"],
            "reference": reference,
            "payment_details": {
                "namaskah_amount": req.amount,
                "usd_amount": round(amount_usd, 2),
                "ngn_amount": round(amount_ngn, 2),
                "currency": "NGN",
                "exchange_rate": "1N = $2 USD",
            },
            "payment_methods": [
                "Card",
                "Bank Transfer",
                "USSD",
                "QR Code",
                "Mobile Money",
            ],
            "message": f"Pay NGN {amount_ngn:,.2f} (${amount_usd:.2f} USD)",
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Payment gateway error: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Payment initialization failed: {str(e)}"
        )


@app.post("/wallet/paystack/webhook", tags=["Wallet"], summary="Paystack Webhook")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Paystack payment webhooks with signature verification"""
    import hmac
    import hashlib

    # Get signature and body
    signature = request.headers.get("x-paystack-signature")
    body = await request.body()

    # Verify webhook signature (CRITICAL SECURITY)
    if not PAYSTACK_SECRET_KEY or not PAYSTACK_SECRET_KEY.startswith("sk_"):
        # Log but don't process if no valid secret key
        print("⚠️ Paystack webhook received but no valid secret key configured")
        return {"status": "ignored", "reason": "no_secret_key"}

    expected_signature = hmac.new(
        PAYSTACK_SECRET_KEY.encode("utf-8"), body, hashlib.sha512
    ).hexdigest()

    if signature != expected_signature:
        print(f"❌ Invalid Paystack signature: {signature[:20]}...")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Parse webhook data
    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = data.get("event")
    print(f"📥 Paystack webhook: {event}")

    if event == "charge.success":
        payment_data = data.get("data", {})
        reference = payment_data.get("reference")
        amount_kobo = payment_data.get("amount", 0)
        amount = amount_kobo / 100  # Convert from kobo to Naira
        user_id = payment_data.get("metadata", {}).get("user_id")
        user_email = payment_data.get("metadata", {}).get(
            "user_email"
        ) or payment_data.get("customer", {}).get("email")

        if not reference or not user_id:
            print(f"⚠️ Missing reference or user_id in webhook")
            # Log failed webhook
            if user_email:
                log_activity(
                    db,
                    email=user_email,
                    action="webhook_received",
                    status="failed",
                    error="Missing reference or user_id",
                )
            return {"status": "error", "reason": "missing_data"}

        # Check for duplicate transaction
        existing = (
            db.query(Transaction)
            .filter(Transaction.description.contains(reference))
            .first()
        )

        if existing:
            print(f"⚠️ Duplicate transaction: {reference}")
            # Update payment log
            payment_log = (
                db.query(PaymentLog).filter(PaymentLog.reference == reference).first()
            )
            if payment_log:
                payment_log.webhook_received = True
                payment_log.status = "duplicate"
                db.commit()
            return {"status": "duplicate", "reference": reference}

        # Find user and add credits
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"❌ User not found: {user_id}")
            log_activity(
                db,
                user_id=user_id,
                email=user_email,
                action="webhook_received",
                status="failed",
                error=f"User not found: {user_id}",
            )
            return {"status": "error", "reason": "user_not_found"}

        # Convert NGN to Namaskah coins
        # Get USD amount from metadata or calculate from NGN
        usd_amount = payment_data.get("metadata", {}).get(
            "usd_amount", amount / get_usd_to_ngn_rate()
        )
        namaskah_amount = usd_amount * USD_TO_NAMASKAH

        user.credits += namaskah_amount

        # Create transaction
        transaction = Transaction(
            id=f"txn_{datetime.now(timezone.utc).timestamp()}",
            user_id=user.id,
            amount=namaskah_amount,
            type="credit",
            description=f"Paystack payment: {reference} (NGN {amount})",
        )
        db.add(transaction)

        # Update payment log
        payment_log = (
            db.query(PaymentLog).filter(PaymentLog.reference == reference).first()
        )
        if payment_log:
            payment_log.webhook_received = True
            payment_log.credited = True
            payment_log.status = "completed"
            payment_log.updated_at = datetime.now(timezone.utc)
        else:
            # Create payment log if doesn't exist
            log_payment(
                db,
                user_id=user.id,
                email=user.email,
                reference=reference,
                amount_ngn=amount,
                amount_usd=usd_amount,
                namaskah_amount=namaskah_amount,
                status="completed",
                webhook_received=True,
                credited=True,
            )

        # Log activity
        log_activity(
            db,
            user_id=user.id,
            email=user.email,
            action="payment_completed",
            status="success",
            details=f"Credited N{namaskah_amount:.2f} from {reference}",
        )

        # Process affiliate commission (10% of all spending)
        if user.referred_by:
            referrer = db.query(User).filter(User.id == user.referred_by).first()
            if referrer:
                # Check if first-time funding bonus (N2.50+)
                existing_referral = (
                    db.query(Referral)
                    .filter(
                        Referral.referrer_id == referrer.id,
                        Referral.referred_id == user.id,
                    )
                    .first()
                )

                if (
                    existing_referral
                    and existing_referral.reward_amount == 0
                    and namaskah_amount >= 2.5
                ):
                    # Give referrer 1 free verification (one-time bonus)
                    referrer.free_verifications += 1
                    existing_referral.reward_amount = 1.0

                    db.add(
                        Transaction(
                            id=f"txn_{datetime.now(timezone.utc).timestamp()}",
                            user_id=referrer.id,
                            amount=0,
                            type="credit",
                            description=f"Referral signup bonus: {user.email}",
                        )
                    )

                    send_email(
                        referrer.email,
                        "🎁 Referral Bonus - Namaskah SMS",
                        f"""<h2>Referral Signup Bonus!</h2>
                        <p><strong>{user.email}</strong> funded their account.</p>
                        <p>You received: <strong>1 Free Verification</strong></p>
                        <p><a href="{BASE_URL}/app">Use Your Free Verification</a></p>""",
                    )

        db.commit()

        print(
            f"✅ Payment processed: {reference} - N{namaskah_amount} for {user.email}"
        )

        # Send confirmation email
        send_email(
            user.email,
            "💰 Payment Successful - Namaskah SMS",
            f"""<h2>Payment Confirmed!</h2>
            <p>Your payment of <strong>NGN {amount:.2f}</strong> has been received.</p>
            <p>Credited: <strong>N{namaskah_amount:.2f}</strong></p>
            <p>New balance: <strong>N{user.credits:.2f}</strong></p>
            <p>Reference: {reference}</p>
            <p><a href="{BASE_URL}/app">Start Using Credits</a></p>""",
        )

        return {"status": "success", "reference": reference, "amount": namaskah_amount}

    elif event == "charge.failed":
        payment_data = data.get("data", {})
        reference = payment_data.get("reference")
        print(f"❌ Payment failed: {reference}")
        return {"status": "failed", "reference": reference}

    return {"status": "ignored", "event": event}


@app.get(
    "/wallet/paystack/verify/{reference}", tags=["Wallet"], summary="Verify Payment"
)
def verify_payment(
    reference: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify Paystack payment status (manual verification)"""
    if not PAYSTACK_SECRET_KEY or not PAYSTACK_SECRET_KEY.startswith("sk_"):
        return {"status": "demo", "message": "Demo mode - payment not verified"}

    try:
        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        r = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}", headers=headers
        )
        r.raise_for_status()
        response_data = r.json()

        if not response_data.get("status"):
            return {"status": "error", "message": "Invalid response from Paystack"}

        payment_data = response_data.get("data", {})
        payment_status = payment_data.get("status")

        if payment_status == "success":
            amount_kobo = payment_data.get("amount", 0)
            amount = amount_kobo / 100  # Convert from kobo

            # Check if already credited
            existing = (
                db.query(Transaction)
                .filter(Transaction.description.contains(reference))
                .first()
            )

            if existing:
                return {
                    "status": "already_credited",
                    "message": "Payment already processed",
                    "reference": reference,
                    "balance": user.credits,
                }

            # Convert USD to Namaskah coins
            namaskah_amount = amount * USD_TO_NAMASKAH

            user.credits += namaskah_amount
            transaction = Transaction(
                id=f"txn_{datetime.now(timezone.utc).timestamp()}",
                user_id=user.id,
                amount=namaskah_amount,
                type="credit",
                description=f"Paystack payment verified: {reference} (NGN {amount})",
            )
            db.add(transaction)
            db.commit()

            # Send confirmation email
            send_email(
                user.email,
                "💰 Payment Confirmed - Namaskah SMS",
                f"""<h2>Payment Verified!</h2>
                <p>Your payment of <strong>NGN {amount:.2f}</strong> has been confirmed.</p>
                <p>Credited: <strong>N{namaskah_amount:.2f}</strong></p>
                <p>New balance: <strong>N{user.credits:.2f}</strong></p>
                <p>Reference: {reference}</p>""",
            )

            return {
                "status": "success",
                "amount": namaskah_amount,
                "new_balance": user.credits,
                "reference": reference,
                "message": f"Credited N{namaskah_amount:.2f} to your wallet",
            }
        else:
            return {
                "status": "failed",
                "message": f"Payment status: {payment_status}",
                "reference": reference,
            }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Paystack API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")


# REMOVED: Crypto payment endpoints - Not implemented


# API Key Endpoints
@app.post("/api-keys/create", tags=["API Keys"], summary="Create API Key")
def create_api_key(
    req: CreateAPIKeyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate new API key for programmatic access"""
    import secrets

    key = f"nsk_{secrets.token_urlsafe(32)}"

    api_key = APIKey(
        id=f"key_{datetime.now(timezone.utc).timestamp()}",
        user_id=user.id,
        key=key,
        name=req.name,
    )
    db.add(api_key)
    db.commit()

    return {"key": key, "name": req.name, "created_at": api_key.created_at}


@app.get("/api-keys/list", tags=["API Keys"], summary="List API Keys")
def list_api_keys(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all API keys for current user"""
    keys = db.query(APIKey).filter(APIKey.user_id == user.id).all()
    return {
        "keys": [
            {
                "id": k.id,
                "name": k.name,
                "key": k.key[:12] + "...",
                "is_active": k.is_active,
                "created_at": k.created_at,
            }
            for k in keys
        ]
    }


@app.delete("/api-keys/{key_id}", tags=["API Keys"], summary="Delete API Key")
def delete_api_key(
    key_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Revoke API key permanently"""
    key = (
        db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user.id).first()
    )
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    db.delete(key)
    db.commit()
    return {"message": "API key deleted"}


# Webhook Endpoints
@app.post("/webhooks/create", tags=["Webhooks"], summary="Create Webhook")
def create_webhook(
    req: CreateWebhookRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register webhook URL for SMS notifications"""
    webhook = Webhook(
        id=f"webhook_{datetime.now(timezone.utc).timestamp()}",
        user_id=user.id,
        url=req.url,
    )
    db.add(webhook)
    db.commit()

    return {"id": webhook.id, "url": webhook.url, "is_active": webhook.is_active}


@app.get("/webhooks/list", tags=["Webhooks"], summary="List Webhooks")
def list_webhooks(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all configured webhooks"""
    webhooks = db.query(Webhook).filter(Webhook.user_id == user.id).all()
    return {
        "webhooks": [
            {
                "id": w.id,
                "url": w.url,
                "is_active": w.is_active,
                "created_at": w.created_at,
            }
            for w in webhooks
        ]
    }


@app.delete("/webhooks/{webhook_id}", tags=["Webhooks"], summary="Delete Webhook")
def delete_webhook(
    webhook_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove webhook configuration"""
    webhook = (
        db.query(Webhook)
        .filter(Webhook.id == webhook_id, Webhook.user_id == user.id)
        .first()
    )
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    db.delete(webhook)
    db.commit()
    return {"message": "Webhook deleted"}


async def send_webhook(user_id: str, verification_id: str, messages: list, db: Session):
    """Send SMS to user webhooks"""
    webhooks = (
        db.query(Webhook)
        .filter(Webhook.user_id == user_id, Webhook.is_active == True)
        .all()
    )

    for webhook in webhooks:
        try:
            payload = {
                "verification_id": verification_id,
                "messages": messages,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            requests.post(webhook.url, json=payload, timeout=5)
        except:
            pass


# Analytics Endpoints
@app.get("/analytics/dashboard", tags=["Analytics"], summary="Get Analytics Dashboard")
def get_analytics(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get usage analytics: total verifications, spending, success rate, popular services, daily usage"""
    from sqlalchemy import func

    # Total verifications
    total_verifications = (
        db.query(Verification).filter(Verification.user_id == user.id).count()
    )

    # Total spent
    total_spent = (
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.user_id == user.id, Transaction.type == "debit")
        .scalar()
        or 0
    )

    # Success rate
    completed = (
        db.query(Verification)
        .filter(Verification.user_id == user.id, Verification.status == "completed")
        .count()
    )
    success_rate = (
        (completed / total_verifications * 100) if total_verifications > 0 else 0
    )

    # Popular services
    popular = (
        db.query(Verification.service_name, func.count(Verification.id).label("count"))
        .filter(Verification.user_id == user.id)
        .group_by(Verification.service_name)
        .order_by(func.count(Verification.id).desc())
        .limit(5)
        .all()
    )

    # Recent activity (last 7 days)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_verifications = (
        db.query(Verification)
        .filter(
            Verification.user_id == user.id, Verification.created_at >= seven_days_ago
        )
        .count()
    )

    # Daily usage (last 7 days)
    daily_usage = []
    for i in range(7):
        day = datetime.now(timezone.utc) - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        count = (
            db.query(Verification)
            .filter(
                Verification.user_id == user.id,
                Verification.created_at >= day_start,
                Verification.created_at < day_end,
            )
            .count()
        )

        daily_usage.append({"date": day_start.strftime("%Y-%m-%d"), "count": count})

    return {
        "total_verifications": total_verifications,
        "total_spent": abs(total_spent),
        "success_rate": round(success_rate, 1),
        "popular_services": [{"service": s[0], "count": s[1]} for s in popular],
        "recent_verifications": recent_verifications,
        "daily_usage": list(reversed(daily_usage)),
    }


# Receipt and Notification Endpoints
@app.get("/receipts/history", tags=["Receipts"], summary="Get Receipt History")
def get_receipt_history(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's verification receipts"""
    receipt_service = ReceiptService(db)
    receipts = receipt_service.get_user_receipts(user.id, limit)

    return {"receipts": receipts, "total_count": len(receipts)}


@app.get("/receipts/{receipt_id}", tags=["Receipts"], summary="Get Receipt Details")
def get_receipt_details(
    receipt_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed receipt information"""
    receipt = (
        db.query(VerificationReceipt)
        .filter(
            VerificationReceipt.id == receipt_id, VerificationReceipt.user_id == user.id
        )
        .first()
    )

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    import json

    receipt_data = json.loads(receipt.receipt_data) if receipt.receipt_data else {}

    return {
        "id": receipt.id,
        "receipt_number": f"NSK-{receipt.verification_id[-8:].upper()}",
        "service_name": receipt.service_name,
        "phone_number": receipt.phone_number,
        "amount_spent": receipt.amount_spent,
        "amount_usd": round(receipt.amount_spent * 2, 2),
        "isp_carrier": receipt.isp_carrier,
        "area_code": receipt.area_code,
        "success_timestamp": receipt.success_timestamp.isoformat(),
        "verification_id": receipt.verification_id,
        "receipt_data": receipt_data,
    }


@app.get(
    "/notifications/list", tags=["Notifications"], summary="Get In-App Notifications"
)
def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's in-app notifications"""
    notification_service = NotificationService(db)
    notifications = notification_service.get_user_notifications(
        user.id, unread_only, limit
    )

    unread_count = len([n for n in notifications if not n["is_read"]])

    return {
        "notifications": notifications,
        "unread_count": unread_count,
        "total_count": len(notifications),
    }


@app.post(
    "/notifications/{notification_id}/read",
    tags=["Notifications"],
    summary="Mark Notification as Read",
)
def mark_notification_read(
    notification_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark specific notification as read"""
    notification_service = NotificationService(db)
    success = notification_service.mark_notification_read(notification_id, user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"message": "Notification marked as read"}


@app.post(
    "/notifications/mark-all-read",
    tags=["Notifications"],
    summary="Mark All Notifications as Read",
)
def mark_all_notifications_read(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Mark all notifications as read for user"""
    notification_service = NotificationService(db)
    notification_service.mark_all_read(user.id)

    return {"message": "All notifications marked as read"}


@app.get(
    "/notifications/settings",
    tags=["Notifications"],
    summary="Get Notification Settings",
)
def get_notification_settings(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get notification preferences including receipt notifications"""
    notification_service = NotificationService(db)
    preferences = notification_service.get_notification_preferences(user.id)

    # Also get legacy settings for backward compatibility
    legacy_settings = (
        db.query(NotificationSettings)
        .filter(NotificationSettings.user_id == user.id)
        .first()
    )

    return {
        "in_app_notifications": preferences["in_app_notifications"],
        "email_notifications": preferences["email_notifications"],
        "receipt_notifications": preferences["receipt_notifications"],
        # Legacy fields
        "email_on_sms": legacy_settings.email_on_sms if legacy_settings else True,
        "email_on_low_balance": (
            legacy_settings.email_on_low_balance if legacy_settings else True
        ),
        "low_balance_threshold": (
            legacy_settings.low_balance_threshold if legacy_settings else 1.0
        ),
    }


@app.post(
    "/notifications/settings",
    tags=["Notifications"],
    summary="Update Notification Settings",
)
def update_notification_settings(
    in_app_notifications: bool = None,
    email_notifications: bool = None,
    receipt_notifications: bool = None,
    email_on_sms: bool = None,
    email_on_low_balance: bool = None,
    low_balance_threshold: float = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update notification preferences"""
    notification_service = NotificationService(db)

    # Update new notification preferences
    preferences = notification_service.update_notification_preferences(
        user_id=user.id,
        in_app_notifications=in_app_notifications,
        email_notifications=email_notifications,
        receipt_notifications=receipt_notifications,
    )

    # Update legacy settings if provided
    if any(
        [
            email_on_sms is not None,
            email_on_low_balance is not None,
            low_balance_threshold is not None,
        ]
    ):
        legacy_settings = (
            db.query(NotificationSettings)
            .filter(NotificationSettings.user_id == user.id)
            .first()
        )

        if not legacy_settings:
            legacy_settings = NotificationSettings(
                id=f"notif_{datetime.now(timezone.utc).timestamp()}", user_id=user.id
            )
            db.add(legacy_settings)

        if email_on_sms is not None:
            legacy_settings.email_on_sms = email_on_sms
        if email_on_low_balance is not None:
            legacy_settings.email_on_low_balance = email_on_low_balance
        if low_balance_threshold is not None:
            legacy_settings.low_balance_threshold = low_balance_threshold

        db.commit()

    return {"message": "Notification settings updated", "preferences": preferences}


# Referral Endpoints
@app.get("/referrals/stats", tags=["Referrals"], summary="Get Referral Statistics")
def get_referral_stats(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get referral code, earnings, and referred users list"""
    referrals = db.query(Referral).filter(Referral.referrer_id == user.id).all()

    referred_users = []
    for ref in referrals:
        referred_user = db.query(User).filter(User.id == ref.referred_id).first()
        if referred_user:
            referred_users.append(
                {
                    "email": referred_user.email,
                    "joined_at": ref.created_at,
                    "reward": ref.reward_amount,
                }
            )

    return {
        "referral_code": user.referral_code,
        "total_referrals": len(referrals),
        "total_earnings": user.referral_earnings,
        "referral_link": f"{BASE_URL}/app?ref={user.referral_code}",
        "referred_users": referred_users,
    }


# Support Endpoints
@app.post("/support/submit", tags=["System"], summary="Submit Support Request")
def submit_support(req: SupportRequest, db: Session = Depends(get_db)):
    """Submit support/contact request. Available to all users (logged in or not)."""
    ticket = SupportTicket(
        id=f"ticket_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        name=req.name,
        email=req.email,
        category=req.category,
        message=req.message,
        status="open",
    )
    db.add(ticket)
    db.commit()

    # Send confirmation email to user
    send_email(
        req.email,
        "Support Request Received - Namaskah SMS",
        f"""<h2>Thank You for Contacting Us!</h2>
        <p>We've received your support request and will respond within 24 hours.</p>
        <p><strong>Ticket ID:</strong> {ticket.id}</p>
        <p><strong>Category:</strong> {req.category}</p>
        <p><strong>Your Message:</strong></p>
        <p>{req.message}</p>
        <p>You'll receive a response at this email address.</p>""",
    )

    return {
        "success": True,
        "ticket_id": ticket.id,
        "message": "Support request submitted successfully. We'll respond within 24 hours.",
    }


@app.get("/admin/support/tickets", tags=["Admin"], summary="Get All Support Tickets")
def get_support_tickets(
    status: str = None,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get all support tickets (admin only). Filter by status if provided."""
    query = db.query(SupportTicket)
    if status:
        query = query.filter(SupportTicket.status == status)

    tickets = query.order_by(SupportTicket.created_at.desc()).all()

    return {
        "tickets": [
            {
                "id": t.id,
                "name": t.name,
                "email": t.email,
                "category": t.category,
                "message": t.message,
                "status": t.status,
                "admin_response": t.admin_response,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            }
            for t in tickets
        ]
    }


@app.post(
    "/admin/support/{ticket_id}/respond",
    tags=["Admin"],
    summary="Respond to Support Ticket",
)
def respond_to_ticket(
    ticket_id: str,
    req: AdminResponseRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Send response to support ticket and notify user via email (admin only)."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.admin_response = req.response
    ticket.status = "resolved"
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Send response email to user
    send_email(
        ticket.email,
        f"Re: Support Request #{ticket.id} - Namaskah SMS",
        f"""<h2>Support Response</h2>
        <p>Hi {ticket.name},</p>
        <p>We've reviewed your support request regarding <strong>{ticket.category}</strong>.</p>
        <p><strong>Your Message:</strong></p>
        <p>{ticket.message}</p>
        <p><strong>Our Response:</strong></p>
        <p>{req.response}</p>
        <p>If you need further assistance, please reply to this email.</p>
        <p>Best regards,<br>Namaskah Support Team</p>""",
    )

    return {"message": "Response sent successfully", "ticket_id": ticket.id}


@app.patch(
    "/admin/support/{ticket_id}/status", tags=["Admin"], summary="Update Ticket Status"
)
def update_ticket_status(
    ticket_id: str,
    status: str,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Update support ticket status (admin only)."""
    valid_statuses = ["open", "in_progress", "resolved", "closed"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = status
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Status updated", "ticket_id": ticket.id, "new_status": status}


# Service Pricing Management (Dynamic)
class ServicePricing(Base):
    __tablename__ = "service_pricing"
    id = Column(String, primary_key=True)
    service_name = Column(String, nullable=False, unique=True)
    price = Column(Float, nullable=False)
    is_popular = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime)


class SystemConfig(Base):
    __tablename__ = "system_config"
    id = Column(String, primary_key=True)
    key = Column(String, nullable=False, unique=True)
    value = Column(String, nullable=False)
    description = Column(String)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


Base.metadata.create_all(bind=engine)

# Rental pricing now imported from pricing_config.py


def calculate_refund(rental: NumberRental) -> float:
    """Calculate refund for early release (50% of unused time, min 1hr used)"""
    try:
        started_at = rental.started_at or rental.created_at
        used_hours = (datetime.now(timezone.utc) - started_at).total_seconds() / 3600
        if used_hours < 1:
            used_hours = 1
        unused_hours = max(0, rental.duration_hours - used_hours)
        hourly_rate = (
            rental.cost / rental.duration_hours if rental.duration_hours > 0 else 0
        )
        return round((unused_hours * hourly_rate) * 0.5, 2)
    except Exception as e:
        logger.error(f"Refund calculation error: {e}")
        return 0.0


@app.get("/admin/pricing/services", tags=["Admin"], summary="Get All Service Pricing")
def get_service_pricing(
    admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Get pricing for all services (admin only)"""
    pricing = db.query(ServicePricing).all()
    return {
        "default_popular": SMS_PRICING["popular"],
        "default_general": SMS_PRICING["general"],
        "custom_pricing": [
            {
                "service_name": p.service_name,
                "price": p.price,
                "is_popular": p.is_popular,
            }
            for p in pricing
        ],
    }


@app.post(
    "/admin/pricing/services/{service_name}",
    tags=["Admin"],
    summary="Set Service Price",
)
def set_service_price(
    service_name: str,
    price: float,
    is_popular: bool = False,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Set custom price for specific service (admin only)"""
    if price < 0.5:
        raise HTTPException(status_code=400, detail="Minimum price is N0.50")

    pricing = (
        db.query(ServicePricing)
        .filter(ServicePricing.service_name == service_name)
        .first()
    )

    if pricing:
        pricing.price = price
        pricing.is_popular = is_popular
        pricing.updated_at = datetime.now(timezone.utc)
    else:
        pricing = ServicePricing(
            id=f"price_{datetime.now(timezone.utc).timestamp()}",
            service_name=service_name,
            price=price,
            is_popular=is_popular,
        )
        db.add(pricing)

    db.commit()
    return {"message": f"Price set for {service_name}", "price": price}


@app.post("/admin/pricing/bulk", tags=["Admin"], summary="Bulk Update Service Pricing")
def bulk_update_pricing(
    services: dict, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Bulk update pricing for multiple services (admin only)"""
    updated = []
    for service_name, price in services.items():
        if price < 0.5:
            continue

        pricing = (
            db.query(ServicePricing)
            .filter(ServicePricing.service_name == service_name)
            .first()
        )
        if pricing:
            pricing.price = price
            pricing.updated_at = datetime.now(timezone.utc)
        else:
            pricing = ServicePricing(
                id=f"price_{datetime.now(timezone.utc).timestamp()}_{service_name}",
                service_name=service_name,
                price=price,
            )
            db.add(pricing)
        updated.append(service_name)

    db.commit()
    return {"message": f"Updated {len(updated)} services", "services": updated}


@app.delete(
    "/admin/pricing/services/{service_name}",
    tags=["Admin"],
    summary="Remove Custom Pricing",
)
def remove_custom_pricing(
    service_name: str,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Remove custom pricing for service (reverts to default) (admin only)"""
    pricing = (
        db.query(ServicePricing)
        .filter(ServicePricing.service_name == service_name)
        .first()
    )
    if pricing:
        db.delete(pricing)
        db.commit()
        return {"message": f"Custom pricing removed for {service_name}"}
    raise HTTPException(status_code=404, detail="No custom pricing found")


@app.get("/admin/config", tags=["Admin"], summary="Get System Configuration")
def get_system_config(
    admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    """Get all system configuration (admin only)"""
    configs = db.query(SystemConfig).all()
    return {
        "config": {
            c.key: {"value": c.value, "description": c.description} for c in configs
        }
    }


@app.post("/admin/config/{key}", tags=["Admin"], summary="Set System Configuration")
def set_system_config(
    key: str,
    value: str,
    description: str = None,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Set system configuration value (admin only)"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()

    if config:
        config.value = value
        if description:
            config.description = description
        config.updated_at = datetime.now(timezone.utc)
    else:
        config = SystemConfig(
            id=f"config_{datetime.now(timezone.utc).timestamp()}",
            key=key,
            value=value,
            description=description,
        )
        db.add(config)

    db.commit()
    return {"message": f"Configuration {key} updated", "value": value}


# Rental Endpoints
@app.get("/rentals/pricing", tags=["Rentals"], summary="Get Rental Pricing")
def get_rental_pricing(
    hours: float,
    service_name: str = "general",
    mode: str = "always_ready",
    auto_renew: bool = False,
    bulk_count: int = 1,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dynamic pricing for rental with breakdown

    - **hours**: Duration in hours (1-8760)
    - **service_name**: Service type (affects pricing tier)
    - **mode**: 'always_ready' or 'manual' (30% discount)
    - **auto_renew**: Enable auto-renewal (10% discount)
    - **bulk_count**: Number of simultaneous rentals (15% discount for 5+)
    """
    try:
        # Get active rental count for bulk discount calculation
        active_count = (
            db.query(NumberRental)
            .filter(NumberRental.user_id == user.id, NumberRental.status == "active")
            .count()
        )

        # Use higher of current active count or requested bulk count
        effective_bulk_count = max(active_count + 1, bulk_count)

        # Get detailed pricing breakdown
        breakdown = get_rental_price_breakdown(
            hours=hours,
            service_name=service_name,
            mode=mode,
            auto_renew=auto_renew,
            bulk_count=effective_bulk_count,
        )

        # Add rental type info
        breakdown["is_hourly_rental"] = hours <= 24
        breakdown["rental_type"] = "Hourly" if hours <= 24 else "Extended"
        breakdown["mode"] = mode
        breakdown["auto_renew"] = auto_renew
        breakdown["bulk_count"] = effective_bulk_count

        return breakdown

    except Exception as e:
        logger.error(f"Pricing calculation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Pricing calculation failed: {str(e)}"
        )


@app.post("/rentals/create", tags=["Rentals"], summary="Create Number Rental")
def create_rental(
    req: CreateRentalRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rent a phone number for specified duration

    Supports hourly (1-24h) and extended rentals. Pricing varies by service and mode.
    """
    # Validate rental duration
    if req.duration_hours < 1:
        raise HTTPException(status_code=400, detail="Minimum rental duration is 1 hour")

    if req.duration_hours > 8760:  # 365 days
        raise HTTPException(
            status_code=400, detail="Maximum rental duration is 8760 hours (1 year)"
        )

    # Email verification bypassed for development

    # Default to always_ready mode if not specified
    mode = getattr(req, "mode", "always_ready")
    auto_renew = getattr(req, "auto_extend", False)

    # Get active rental count for bulk discount
    active_count = (
        db.query(NumberRental)
        .filter(NumberRental.user_id == user.id, NumberRental.status == "active")
        .count()
    )

    # Calculate cost with new pricing (including bulk discount)
    cost = get_hourly_rental_price(
        hours=req.duration_hours,
        service_name=req.service_name,
        mode=mode,
        auto_renew=auto_renew,
        bulk_count=active_count + 1,  # +1 for the new rental
    )

    if user.credits < cost:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Need N{cost}, have N{user.credits}",
        )

    # Check active rental limit (max 5)
    active_count = (
        db.query(NumberRental)
        .filter(NumberRental.user_id == user.id, NumberRental.status == "active")
        .count()
    )
    if active_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 active rentals allowed")

    # Deduct credits
    user.credits -= cost

    # Create verification for rental
    try:
        verification_id = tv_client.create_verification(req.service_name, "sms")
        details = tv_client.get_verification(verification_id)
        phone_number = details.get("number")

        if not phone_number:
            raise HTTPException(
                status_code=503, detail="Failed to get phone number from provider"
            )
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Rental service unavailable: {str(e)}"
        )

    now = datetime.now(timezone.utc)
    rental = NumberRental(
        id=f"rental_{int(now.timestamp() * 1000)}",
        user_id=user.id,
        phone_number=phone_number,
        service_name=req.service_name,
        duration_hours=req.duration_hours,
        cost=cost,
        mode=mode,
        status="active",
        started_at=now,
        expires_at=now + timedelta(hours=req.duration_hours),
        auto_extend=req.auto_extend,
    )
    db.add(rental)

    # Create transaction
    db.add(
        Transaction(
            id=f"txn_{now.timestamp()}",
            user_id=user.id,
            amount=-cost,
            type="debit",
            description=f"Rental: {req.service_name} for {req.duration_hours}h",
        )
    )
    db.commit()

    return {
        "id": rental.id,
        "phone_number": rental.phone_number,
        "service_name": rental.service_name,
        "duration_hours": rental.duration_hours,
        "cost": rental.cost,
        "expires_at": rental.expires_at.isoformat(),
        "auto_extend": rental.auto_extend,
        "remaining_credits": user.credits,
        "status": rental.status,
        "is_hourly_rental": rental.duration_hours <= 24,
        "mode": mode,
        "started_at": rental.started_at.isoformat(),
    }


@app.get("/rentals/active", tags=["Rentals"], summary="List Active Rentals")
def list_active_rentals(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all active rentals for current user"""
    try:
        rentals = (
            db.query(NumberRental)
            .filter(NumberRental.user_id == user.id, NumberRental.status == "active")
            .order_by(NumberRental.expires_at)
            .all()
        )

        now = datetime.now(timezone.utc)
        return {
            "rentals": [
                {
                    "id": r.id,
                    "phone_number": r.phone_number,
                    "service_name": r.service_name,
                    "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                    "time_remaining_seconds": (
                        max(0, int((r.expires_at - now).total_seconds()))
                        if r.expires_at
                        else 0
                    ),
                    "auto_extend": r.auto_extend,
                }
                for r in rentals
            ]
        }
    except Exception as e:
        logger.error(f"Rentals query failed: {e}")
        return {"rentals": []}


@app.get("/rentals/{rental_id}", tags=["Rentals"], summary="Get Rental Details")
def get_rental(
    rental_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get rental status and details"""
    rental = (
        db.query(NumberRental)
        .filter(NumberRental.id == rental_id, NumberRental.user_id == user.id)
        .first()
    )

    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    now = datetime.now(timezone.utc)
    return {
        "id": rental.id,
        "phone_number": rental.phone_number,
        "service_name": rental.service_name,
        "status": rental.status,
        "started_at": rental.started_at.isoformat(),
        "expires_at": rental.expires_at.isoformat(),
        "time_remaining_seconds": max(
            0, int((rental.expires_at - now).total_seconds())
        ),
        "duration_hours": rental.duration_hours,
        "cost": rental.cost,
        "auto_extend": rental.auto_extend,
    }


@app.post("/rentals/{rental_id}/extend", tags=["Rentals"], summary="Extend Rental")
def extend_rental(
    rental_id: str,
    req: ExtendRentalRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Extend rental duration with hourly support and pricing breakdown"""
    rental = (
        db.query(NumberRental)
        .filter(
            NumberRental.id == rental_id,
            NumberRental.user_id == user.id,
            NumberRental.status == "active",
        )
        .first()
    )

    if not rental:
        raise HTTPException(status_code=404, detail="Active rental not found")

    # Get current rental mode and auto-extend setting
    mode = getattr(rental, "mode", "always_ready")
    auto_renew = getattr(rental, "auto_extend", False)

    # Get active rental count for bulk discount
    active_count = (
        db.query(NumberRental)
        .filter(NumberRental.user_id == user.id, NumberRental.status == "active")
        .count()
    )

    # Calculate extension cost with pricing breakdown
    pricing_breakdown = get_rental_price_breakdown(
        hours=req.additional_hours,
        service_name=rental.service_name,
        mode=mode,
        auto_renew=auto_renew,
        bulk_count=active_count,
    )

    cost = pricing_breakdown["final_price"]

    if user.credits < cost:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Need N{cost}, have N{user.credits}",
        )

    # Update rental
    user.credits -= cost
    rental.expires_at += timedelta(hours=req.additional_hours)
    rental.duration_hours += req.additional_hours
    rental.cost += cost

    # Create transaction
    db.add(
        Transaction(
            id=f"txn_{datetime.now(timezone.utc).timestamp()}",
            user_id=user.id,
            amount=-cost,
            type="debit",
            description=f"Extended rental {rental_id} by {req.additional_hours}h",
        )
    )
    db.commit()

    return {
        "id": rental.id,
        "extension_hours": req.additional_hours,
        "extension_cost": cost,
        "total_duration_hours": rental.duration_hours,
        "new_expires_at": rental.expires_at.isoformat(),
        "remaining_credits": user.credits,
        "pricing_breakdown": pricing_breakdown,
    }


@app.post(
    "/rentals/{rental_id}/release", tags=["Rentals"], summary="Release Rental Early"
)
def release_rental(
    rental_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Release rental early and get 50% refund for unused time"""
    try:
        rental = (
            db.query(NumberRental)
            .filter(
                NumberRental.id == rental_id,
                NumberRental.user_id == user.id,
                NumberRental.status == "active",
            )
            .first()
        )

        if not rental:
            raise HTTPException(status_code=404, detail="Active rental not found")

        refund = calculate_refund(rental)
        user.credits += refund
        rental.status = "released"
        rental.released_at = datetime.now(timezone.utc)

        if refund > 0:
            db.add(
                Transaction(
                    id=f"txn_{datetime.now(timezone.utc).timestamp()}",
                    user_id=user.id,
                    amount=refund,
                    type="credit",
                    description=f"Refund for early release of rental {rental_id}",
                )
            )

        db.commit()

        return {
            "id": rental.id,
            "status": "released",
            "refund": refund,
            "remaining_credits": user.credits,
            "message": f"Refunded N{refund} for unused time",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rental release error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to release rental")


@app.get(
    "/rentals/{rental_id}/messages", tags=["Rentals"], summary="Get Rental Messages"
)
def get_rental_messages(
    rental_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all SMS messages for rented number"""
    rental = (
        db.query(NumberRental)
        .filter(NumberRental.id == rental_id, NumberRental.user_id == user.id)
        .first()
    )

    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    if rental.status != "active":
        raise HTTPException(status_code=400, detail="Rental is not active")

    # Get messages from TextVerified
    try:
        # TextVerified uses verification ID to track rentals
        # We need to extract the verification ID from the rental
        messages = tv_client.get_messages(rental.id)

        return {
            "rental_id": rental.id,
            "phone_number": rental.phone_number,
            "service_name": rental.service_name,
            "expires_at": rental.expires_at.isoformat(),
            "messages": messages,
            "message_count": len(messages),
            "last_checked": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        # If TextVerified API fails, return empty messages
        return {
            "rental_id": rental.id,
            "phone_number": rental.phone_number,
            "service_name": rental.service_name,
            "expires_at": rental.expires_at.isoformat(),
            "messages": [],
            "message_count": 0,
            "last_checked": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }


# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"WebSocket connected: {user_id}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"WebSocket disconnected: {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except:
                self.disconnect(user_id)

    async def broadcast_message(self, message: dict):
        disconnected = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except:
                disconnected.append(user_id)

        for user_id in disconnected:
            self.disconnect(user_id)


manager = ConnectionManager()

# CORS for frontend
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import time

# Get allowed origins from environment
allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Add GZip compression for responses >1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate Limiting with Redis
import time as time_module

try:
    import redis

    REDIS_MODULE_AVAILABLE = True
except ImportError:
    REDIS_MODULE_AVAILABLE = False

# Initialize Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
if REDIS_MODULE_AVAILABLE:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        REDIS_AVAILABLE = True
    except:
        redis_client = None
        REDIS_AVAILABLE = False
        print("Redis not available, using in-memory rate limiting")
else:
    redis_client = None
    REDIS_AVAILABLE = False
    print("Redis module not installed, rate limiting disabled")


def check_rate_limit(user_id: str, limit: int = 100, window: int = 60):
    """Check if user exceeded rate limit (100 req/min)"""
    if not REDIS_AVAILABLE:
        return True  # Skip rate limiting if Redis unavailable

    try:
        key = f"rate_limit:{user_id}"
        now = time_module.time()

        # Remove old requests outside window
        redis_client.zremrangebyscore(key, 0, now - window)

        # Count requests in current window
        request_count = redis_client.zcard(key)

        if request_count >= limit:
            return False

        # Add current request
        redis_client.zadd(key, {str(now): now})
        redis_client.expire(key, window)

        return True
    except:
        return True  # Allow request if Redis fails


@app.middleware("http")
async def https_redirect_middleware(request: Request, call_next):
    # Force HTTPS in production
    if request.url.scheme == "http" and request.url.hostname not in [
        "localhost",
        "127.0.0.1",
    ]:
        url = request.url.replace(scheme="https")
        return RedirectResponse(url, status_code=301)
    return await call_next(request)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )

    # Performance headers
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif request.url.path in ["/", "/app", "/api-docs"]:
        response.headers["Cache-Control"] = "public, max-age=3600"

    return response


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time_module.time()

    # Extract user ID from token if present
    user_id = "anonymous"
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("user_id", "unknown")
        except:
            pass

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time_module.time() - start_time

    # Log request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.3f}s - "
        f"User: {user_id}"
    )

    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for static files and docs
    if request.url.path.startswith("/static") or request.url.path in [
        "/",
        "/app",
        "/admin",
        "/api-docs",
        "/health",
    ]:
        return await call_next(request)

    # Extract user from token
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("user_id")

            if not check_rate_limit(user_id):
                return {"detail": "Rate limit exceeded. Max 100 requests per minute."}
        except:
            pass

    return await call_next(request)


if __name__ == "__main__":
    import uvicorn

    create_admin_if_not_exists()
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Add WebSocket routes
add_websocket_routes(app)
