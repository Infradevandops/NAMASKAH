"""Namaskah SMS - With Pricing & Admin Panel"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

import jwt
from dotenv import load_dotenv
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Float
from error_handlers import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    log_transaction,
    log_security_event,
    logger
)

from sqlalchemy.orm import sessionmaker, Session
import bcrypt
import requests

load_dotenv()

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
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sms.db")
TEXTVERIFIED_API_KEY = os.getenv("TEXTVERIFIED_API_KEY")
TEXTVERIFIED_EMAIL = os.getenv("TEXTVERIFIED_EMAIL")

# Currency: 1N = $2 USD
USD_TO_NAMASKAH = 0.5  # 1 USD = 0.5N
NAMASKAH_TO_USD = 2.0  # 1N = 2 USD

# SMS Verification Pricing (in Namaskah coins N)
SMS_PRICING = {
    'popular': 1.0,        # WhatsApp, Instagram, Facebook, Telegram, etc.
    'general': 1.25        # Unlisted services
}

# Voice adds N0.25 to SMS price
VOICE_PREMIUM = 0.25

# Subscription Plans
SUBSCRIPTION_PLANS = {
    'starter': {
        'name': 'Starter',
        'duration': 7,  # 7 days
        'price': 12.5,  # N12.5 = $25
        'discount': 0.0,  # No discount
        'area_code': False,
        'carrier': False,
        'description': 'Random numbers, 7 days'
    },
    'pro': {
        'name': 'Pro',
        'duration': 30,  # 30 days (1 month)
        'price': 25.0,  # N25 = $50
        'discount': 0.20,  # 20% discount
        'area_code': True,
        'carrier': False,
        'description': 'Choose area code, 30 days, 20% discount'
    },
    'turbo': {
        'name': 'Turbo',
        'duration': 0,  # Lifetime
        'price': 75.0,  # N75 = $150
        'discount': 0.35,  # 35% discount
        'area_code': True,
        'carrier': True,
        'description': 'Choose area code + carrier, lifetime, 35% discount'
    }
}

VERIFICATION_COST = SMS_PRICING['popular']  # Default
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Payment Config
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
BITCOIN_ADDRESS = os.getenv("BITCOIN_ADDRESS", "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh")
ETHEREUM_ADDRESS = os.getenv("ETHEREUM_ADDRESS", "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
SOLANA_ADDRESS = os.getenv("SOLANA_ADDRESS", "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU")
USDT_ADDRESS = os.getenv("USDT_ADDRESS", "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")

# Exchange rate cache (updates every 1 hour)
exchange_rate_cache = {"rate": 1478.24, "last_updated": None}

def get_usd_to_ngn_rate():
    """Get current USD to NGN exchange rate with 1-hour caching"""
    from datetime import datetime, timedelta, timezone
    
    now = datetime.now(timezone.utc)
    
    # Check if cache is valid (less than 1 hour old)
    if exchange_rate_cache["last_updated"] and \
       (now - exchange_rate_cache["last_updated"]) < timedelta(hours=1):
        return exchange_rate_cache["rate"]
    
    # Fetch new rate
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
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
        pool_recycle=3600
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
    started_at = Column(DateTime, nullable=False)
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

Base.metadata.create_all(bind=engine)

# Create database indexes for performance
def create_indexes():
    """Create indexes on frequently queried fields"""
    try:
        with engine.connect() as conn:
            # User indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)")
            
            # Verification indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_verifications_user_id ON verifications(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_verifications_status ON verifications(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_verifications_created_at ON verifications(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_verifications_service_name ON verifications(service_name)")
            
            # Transaction indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at)")
            
            # Rental indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rentals_user_id ON number_rentals(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rentals_status ON number_rentals(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rentals_expires_at ON number_rentals(expires_at)")
            
            # Service status indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_service_status_name ON service_status(service_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_service_status_checked ON service_status(last_checked)")
            
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
            admin = User(
                id=f"user_{datetime.now(timezone.utc).timestamp()}",
                email="admin@namaskah.app",
                password_hash=bcrypt.hashpw(b"Namaskah@Admin2024", bcrypt.gensalt()).decode(),
                credits=100.0,
                free_verifications=0.0,
                is_admin=True,
                email_verified=True,
                referral_code=secrets.token_urlsafe(6)
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
            status_record = db.query(ServiceStatus).filter(
                ServiceStatus.service_name == "textverified_api"
            ).first()
            
            if status_record:
                status_record.status = status
                status_record.last_checked = datetime.now(timezone.utc)
            else:
                status_record = ServiceStatus(
                    id=f"status_textverified_api_{datetime.now(timezone.utc).timestamp()}",
                    service_name="textverified_api",
                    status=status,
                    success_rate=100.0 if status == "operational" else 0.0
                )
                db.add(status_record)
            
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Health check error: {e}")
        
        # Wait 5 minutes
        await asyncio.sleep(300)

# Email Helper
def send_email(to_email: str, subject: str, body: str):
    """Send email notification"""
    if not SMTP_HOST or not SMTP_USER:
        return  # Email not configured
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Email error: {e}")

# Activity Logging Helper
def log_activity(db: Session, user_id=None, email=None, page=None, action=None, element=None, status=None, details=None, error=None, ip=None, user_agent=None):
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
            user_agent=user_agent
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"Activity log error: {e}")

# Payment Logging Helper
def log_payment(db: Session, user_id=None, email=None, reference=None, amount_ngn=0, amount_usd=0, namaskah_amount=0, status="initialized", **kwargs):
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
            **kwargs
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

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
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

    def get_token(self):
        if self.token:
            return self.token
        headers = {"X-API-KEY": self.api_key, "X-API-USERNAME": self.email}
        r = requests.post(f"{self.base_url}/api/pub/v2/auth", headers=headers)
        r.raise_for_status()
        self.token = r.json()["token"]
        return self.token

    def create_verification(self, service_name: str, capability: str = "sms", area_code: str = None, carrier: str = None):
        headers = {"Authorization": f"Bearer {self.get_token()}"}
        payload = {"serviceName": service_name, "capability": capability}
        
        # Add filters if provided
        if area_code:
            payload["areaCode"] = area_code
        if carrier:
            payload["carrier"] = carrier
        
        r = requests.post(
            f"{self.base_url}/api/pub/v2/verifications",
            headers=headers,
            json=payload
        )
        r.raise_for_status()
        return r.headers.get("Location", "").split("/")[-1]

    def get_verification(self, verification_id: str):
        headers = {"Authorization": f"Bearer {self.get_token()}"}
        r = requests.get(f"{self.base_url}/api/pub/v2/verifications/{verification_id}", headers=headers)
        r.raise_for_status()
        return r.json()

    def get_messages(self, verification_id: str):
        headers = {"Authorization": f"Bearer {self.get_token()}"}
        r = requests.get(f"{self.base_url}/api/pub/v2/sms?reservationId={verification_id}", headers=headers)
        r.raise_for_status()
        return [sms["smsContent"] for sms in r.json().get("data", [])]

    def cancel_verification(self, verification_id: str):
        headers = {"Authorization": f"Bearer {self.get_token()}"}
        r = requests.post(f"{self.base_url}/api/pub/v2/verifications/{verification_id}/cancel", headers=headers)
        r.raise_for_status()
        return True

tv_client = TextVerifiedClient()

# FastAPI App
app = FastAPI(
    title="Namaskah SMS API",
    version="2.2.0",
    description="""🚀 **Simple SMS Verification Service**

Namaskah SMS provides temporary phone numbers for SMS verification across 1,807+ services.

## Features
- 📱 1,807+ supported services (WhatsApp, Telegram, Google, etc.)
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
        "url": "https://namaskah.app"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {"name": "Authentication", "description": "User registration, login, and OAuth"},
        {"name": "Verification", "description": "Create and manage SMS verifications"},
        {"name": "Rentals", "description": "Long-term number rentals (hourly/daily/weekly)"},
        {"name": "Wallet", "description": "Fund wallet and manage credits"},
        {"name": "Admin", "description": "Admin-only endpoints (requires admin role)"},
        {"name": "API Keys", "description": "Manage API keys for programmatic access"},
        {"name": "Webhooks", "description": "Configure webhook notifications"},
        {"name": "Analytics", "description": "Usage statistics and insights"},
        {"name": "Notifications", "description": "Email notification settings"},
        {"name": "Referrals", "description": "Referral program and earnings"},
        {"name": "System", "description": "Health checks and service info"}
    ]
)

# Register error handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Register startup event
@app.on_event("startup")
async def startup_event():
    """Run background tasks on startup"""
    import asyncio
    asyncio.create_task(check_textverified_health_loop())
    
    # Auto-fix admin password
    try:
        db = SessionLocal()
        admin = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if admin:
            try:
                bcrypt.checkpw(b"Namaskah@Admin2024", admin.password_hash.encode('utf-8'))
                print("✅ Admin password OK")
            except:
                admin.password_hash = bcrypt.hashpw(b"Namaskah@Admin2024", bcrypt.gensalt()).decode()
                admin.is_admin = True
                db.commit()
                print("✅ Admin password auto-fixed")
        else:
            # Create admin if doesn't exist
            import secrets
            admin = User(
                id=f"user_{datetime.now(timezone.utc).timestamp()}",
                email="admin@namaskah.app",
                password_hash=bcrypt.hashpw(b"Namaskah@Admin2024", bcrypt.gensalt()).decode(),
                credits=100.0,
                is_admin=True,
                email_verified=True,
                referral_code=secrets.token_urlsafe(6)
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
    response = templates.TemplateResponse("landing.html", {"request": request})
    response.headers["Cache-Control"] = "no-cache"
    return response

@app.get("/app")
async def app_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api-docs")
async def api_docs_page(request: Request):
    return templates.TemplateResponse("api_docs.html", {"request": request})

@app.get("/faq")
async def faq_page(request: Request):
    return templates.TemplateResponse("faq.html", {"request": request})

@app.get("/about")
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/reviews")
async def reviews_page(request: Request):
    return templates.TemplateResponse("reviews.html", {"request": request})

@app.get("/status")
async def status_page(request: Request):
    return templates.TemplateResponse("status.html", {"request": request})

@app.get("/admin")
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/analytics")
async def analytics_page(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})

@app.get("/manifest.json")
async def manifest():
    """Serve PWA manifest"""
    from fastapi.responses import FileResponse
    return FileResponse("static/manifest.json", media_type="application/json")

@app.get("/sw.js")
async def service_worker():
    """Serve service worker"""
    from fastapi.responses import FileResponse
    return FileResponse("static/sw.js", media_type="application/javascript")

@app.get("/health", tags=["System"], summary="Health Check")
def health():
    return {
        "status": "healthy",
        "service": "namaskah-sms",
        "version": "2.0.0",
        "database": "connected",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/emergency-admin-reset", tags=["System"], summary="Emergency Admin Reset")
def emergency_admin_reset(secret: str, db: Session = Depends(get_db)):
    """Emergency endpoint to reset admin password - remove after use"""
    if secret != "NAMASKAH_EMERGENCY_2024":
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    try:
        admin = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if admin:
            admin.password_hash = bcrypt.hashpw(b"Namaskah@Admin2024", bcrypt.gensalt()).decode()
            admin.is_admin = True
            admin.email_verified = True
            db.commit()
            return {"status": "success", "message": "Admin password reset to Namaskah@Admin2024"}
        else:
            import secrets
            admin = User(
                id=f"user_{datetime.now(timezone.utc).timestamp()}",
                email="admin@namaskah.app",
                password_hash=bcrypt.hashpw(b"Namaskah@Admin2024", bcrypt.gensalt()).decode(),
                credits=100.0,
                is_admin=True,
                email_verified=True,
                referral_code=secrets.token_urlsafe(6)
            )
            db.add(admin)
            db.commit()
            return {"status": "success", "message": "Admin user created with password Namaskah@Admin2024"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/services/list", tags=["System"], summary="List All Services")
def get_services_list():
    """Get complete list of supported services with categories and pricing
    
    Returns:
    - categories: Services grouped by category
    - uncategorized: Services without category
    - pricing: Cost per verification type
    """
    try:
        import json
        with open('services_categorized.json', 'r') as f:
            data = json.load(f)
        return data
    except:
        return {"categories": {}, "uncategorized": [], "pricing": {"categorized": 0.50, "uncategorized": 0.75}}

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
        with open('services_categorized.json', 'r') as f:
            data = json.load(f)
        
        # Check recent verifications (last 24 hours) for each service
        from sqlalchemy import func
        from datetime import timedelta
        
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Get success rates per service from verifications
        service_stats = db.query(
            Verification.service_name,
            func.count(Verification.id).label('total'),
            func.sum(func.case((Verification.status == 'completed', 1), else_=0)).label('completed')
        ).filter(
            Verification.created_at >= twenty_four_hours_ago
        ).group_by(Verification.service_name).all()
        
        status_map = {}
        down_count = 0
        degraded_count = 0
        
        for stat in service_stats:
            if stat.total > 0:
                success_rate = (stat.completed / stat.total) * 100
                
                # Determine status
                if success_rate < 50:
                    service_status = 'down'
                    down_count += 1
                elif success_rate < 85:
                    service_status = 'degraded'
                    degraded_count += 1
                else:
                    service_status = 'operational'
                
                status_map[stat.service_name] = service_status
                
                # Update or create service status record
                status_record = db.query(ServiceStatus).filter(
                    ServiceStatus.service_name == stat.service_name
                ).first()
                
                if status_record:
                    status_record.status = service_status
                    status_record.success_rate = success_rate
                    status_record.last_checked = datetime.now(timezone.utc)
                else:
                    status_record = ServiceStatus(
                        id=f"status_{stat.service_name}_{datetime.now(timezone.utc).timestamp()}",
                        service_name=stat.service_name,
                        status=service_status,
                        success_rate=success_rate
                    )
                    db.add(status_record)
        
        db.commit()
        
        # Determine overall status
        if down_count > 5:
            overall_status = 'down'
        elif down_count > 0 or degraded_count > 3:
            overall_status = 'degraded'
        else:
            overall_status = 'operational'
        
        return {
            "categories": data.get("categories", {}),
            "status": status_map,
            "overall_status": overall_status,
            "stats": {
                "down": down_count,
                "degraded": degraded_count,
                "operational": len(service_stats) - down_count - degraded_count
            },
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        # Default to all operational if error
        return {
            "categories": {},
            "status": {},
            "overall_status": "operational",
            "stats": {"down": 0, "degraded": 0, "operational": 0},
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

@app.get("/services/status/history", tags=["System"], summary="Get Service Status History")
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
                "checked_at": s.last_checked.isoformat()
            }
            for s in statuses
        ]
    }

@app.post("/auth/register", tags=["Authentication"], summary="Register New User")
def register(req: RegisterRequest, referral_code: str = None, db: Session = Depends(get_db)):
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
    
    user = User(
        id=f"user_{datetime.now(timezone.utc).timestamp()}",
        email=req.email,
        password_hash=bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt()).decode(),
        credits=0.0,
        free_verifications=1.0,
        referral_code=user_referral_code,
        email_verified=False,
        verification_token=verification_token
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
                reward_amount=1.0
            )
            db.add(referral)
            
            # Transactions will be created when referred user funds wallet
    
    db.add(user)
    db.commit()
    
    # Log registration
    log_activity(db, user_id=user.id, email=user.email, action="register", status="success", details=f"New user registered")
    
    # Send verification email
    verification_url = f"{BASE_URL}/auth/verify?token={verification_token}"
    send_email(
        user.email,
        "Verify Your Email - Namaskah SMS",
        f"""<h2>Welcome to Namaskah SMS!</h2>
        <p>Click the link below to verify your email:</p>
        <p><a href="{verification_url}">Verify Email</a></p>
        <p>Or copy this link: {verification_url}</p>
        <p>This link expires in 24 hours.</p>"""
    )
    
    token = jwt.encode({"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(days=30)}, JWT_SECRET, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return {"token": token, "user_id": user.id, "credits": user.credits, "free_verifications": user.free_verifications, "referral_code": user.referral_code, "email_verified": False}

@app.get("/auth/google/config", tags=["Authentication"], summary="Get Google OAuth Config")
def get_google_config():
    """Get Google OAuth configuration"""
    return {
        "client_id": GOOGLE_CLIENT_ID if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_ID != "your-google-client-id.apps.googleusercontent.com" else None
    }

@app.post("/auth/google", tags=["Authentication"], summary="Google OAuth Login")
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate with Google OAuth"""
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            req.token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        
        email = idinfo['email']
        google_id = idinfo['sub']
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new user
            import secrets
            user = User(
                id=f"user_{datetime.now(timezone.utc).timestamp()}",
                email=email,
                password_hash=bcrypt.hashpw(google_id.encode('utf-8'), bcrypt.gensalt()).decode(),  # Use Google ID as password
                credits=0.0,
                free_verifications=1.0,
                referral_code=secrets.token_urlsafe(6)
            )
            db.add(user)
            db.commit()
        
        # Generate JWT
        token = jwt.encode(
            {"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(days=30)},
            JWT_SECRET,
            algorithm="HS256"
        )
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        return {
            "token": token,
            "user_id": user.id,
            "credits": user.credits,
            "is_admin": user.is_admin
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Google authentication failed: {str(e)}")

@app.post("/auth/login", tags=["Authentication"], summary="Login User")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password
    
    Returns JWT token valid for 30 days.
    """
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    try:
        password_valid = bcrypt.checkpw(req.password.encode('utf-8'), user.password_hash.encode('utf-8'))
    except Exception as e:
        print(f"Password verify error: {e}")
        password_valid = False
    
    if not password_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Log login
    try:
        log_activity(db, user_id=user.id, email=user.email, action="login", status="success")
    except:
        pass  # Don't fail login if logging fails
    
    token = jwt.encode({"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(days=30)}, JWT_SECRET, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return {"token": token, "user_id": user.id, "credits": user.credits, "is_admin": user.is_admin}

@app.get("/auth/verify", tags=["Authentication"], summary="Verify Email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email address using token from registration email"""
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    
    user.email_verified = True
    user.verification_token = None
    db.commit()
    
    return {"message": "Email verified successfully"}

@app.post("/auth/resend-verification", tags=["Authentication"], summary="Resend Verification Email")
def resend_verification(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Resend email verification link"""
    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    import secrets
    verification_token = secrets.token_urlsafe(32)
    user.verification_token = verification_token
    db.commit()
    
    verification_url = f"{BASE_URL}/auth/verify?token={verification_token}"
    send_email(
        user.email,
        "Verify Your Email - Namaskah SMS",
        f"""<h2>Verify Your Email</h2>
        <p>Click the link below to verify your email:</p>
        <p><a href="{verification_url}">Verify Email</a></p>"""
    )
    
    return {"message": "Verification email sent"}

@app.post("/auth/forgot-password", tags=["Authentication"], summary="Request Password Reset")
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
    
    reset_url = f"{BASE_URL}/auth/reset-password?token={reset_token}"
    send_email(
        user.email,
        "Reset Your Password - Namaskah SMS",
        f"""<h2>Reset Your Password</h2>
        <p>Click the link below to reset your password:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
        <p>This link expires in 1 hour.</p>"""
    )
    
    return {"message": "If email exists, reset link sent"}

@app.post("/auth/reset-password", tags=["Authentication"], summary="Reset Password")
def reset_password(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Reset password using token from reset email"""
    user = db.query(User).filter(User.reset_token == req.token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    user.password_hash = bcrypt.hashpw(req.new_password.encode('utf-8'), bcrypt.gensalt()).decode()
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    return {"message": "Password reset successfully"}

@app.get("/auth/me", tags=["Authentication"], summary="Get Current User")
def get_me(user: User = Depends(get_current_user)):
    """Get authenticated user information and credit balance"""
    credits = user.credits
    
    # If admin, show real TextVerified balance
    if user.is_admin:
        try:
            token = tv_client.get_token()
            import requests
            headers = {"Authorization": f"Bearer {token}"}
            r = requests.get(f"{tv_client.base_url}/api/pub/v2/account/me", headers=headers)
            data = r.json()
            credits = data.get("currentBalance", user.credits)
        except:
            pass
    
    return {
        "id": user.id,
        "email": user.email,
        "credits": credits,
        "free_verifications": user.free_verifications,
        "is_admin": user.is_admin,
        "email_verified": user.email_verified,
        "created_at": user.created_at
    }

@app.get("/verifications/history", tags=["Verification"], summary="Get Verification History")
def get_history(
    service: str = None,
    status: str = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get verification history with filtering for current user"""
    query = db.query(Verification).filter(Verification.user_id == user.id)
    
    # Filter by service
    if service:
        query = query.filter(Verification.service_name == service)
    
    # Filter by status
    if status and status in ['pending', 'completed', 'cancelled']:
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
                "created_at": v.created_at.isoformat()
            }
            for v in verifications
        ]
    }

@app.get("/verifications/export", tags=["Verification"], summary="Export Verifications to CSV")
def export_user_verifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Export user's verifications to CSV"""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    verifications = db.query(Verification).filter(
        Verification.user_id == user.id
    ).order_by(Verification.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Date', 'Service', 'Phone Number', 'Type', 'Status', 'Cost (N)'])
    
    # Data
    for v in verifications:
        writer.writerow([
            v.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            v.service_name,
            v.phone_number or 'N/A',
            v.capability.upper(),
            v.status.upper(),
            f"{v.cost:.2f}"
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=verifications_{user.id}.csv"}
    )

@app.get("/transactions/history", tags=["Wallet"], summary="Get Transaction History")
def get_transactions(
    type: str = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction history with filtering (credits/debits) for current user"""
    query = db.query(Transaction).filter(Transaction.user_id == user.id)
    
    # Filter by type
    if type and type in ['credit', 'debit']:
        query = query.filter(Transaction.type == type)
    
    transactions = query.order_by(Transaction.created_at.desc()).limit(limit).all()
    
    return {
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "type": t.type,
                "description": t.description,
                "created_at": t.created_at.isoformat()
            }
            for t in transactions
        ]
    }

@app.get("/transactions/export", tags=["Wallet"], summary="Export Transactions to CSV")
def export_user_transactions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Export user's transactions to CSV"""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user.id
    ).order_by(Transaction.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Date', 'Type', 'Amount (N)', 'Description'])
    
    # Data
    for t in transactions:
        writer.writerow([
            t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            t.type.upper(),
            f"{t.amount:.2f}",
            t.description
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=transactions_{user.id}.csv"}
    )

@app.post("/verify/create", tags=["Verification"], summary="Create SMS/Voice Verification")
def create_verification(req: CreateVerificationRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create new SMS or voice verification
    
    - **service_name**: Service identifier (e.g., 'whatsapp', 'telegram')
    - **capability**: 'sms' or 'voice'
    
    Pricing: Popular services N1 ($2), General N1.25 ($2.50), Voice +N0.25
    Tiers: Pay-as-You-Go (no discount), Developer (20% off, min N25), Enterprise (35% off, min N100)
    """
    # Determine base price (popular vs general)
    popular_services = ['whatsapp', 'instagram', 'facebook', 'telegram', 'twitter', 'tiktok', 'snapchat', 'google']
    is_popular = req.service_name.lower() in popular_services
    base_cost = SMS_PRICING['popular'] if is_popular else SMS_PRICING['general']
    
    # Add voice premium if voice verification
    if req.capability == 'voice':
        base_cost += VOICE_PREMIUM
    
    # Get user's subscription plan
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active"
    ).first()
    
    # Apply discount based on subscription
    if subscription:
        discount = SUBSCRIPTION_PLANS[subscription.plan]['discount']
        cost = round(base_cost * (1 - discount), 2)
    else:
        # No subscription = Starter plan (no discount)
        cost = base_cost
    
    # Check if user has free verifications or credits
    if user.free_verifications >= 1:
        user.free_verifications -= 1
        cost = 0  # Free verification
    elif user.credits < cost:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need N{cost}, have N{user.credits}")
    else:
        user.credits -= cost
    
    # Check low balance and send notification
    settings = db.query(NotificationSettings).filter(NotificationSettings.user_id == user.id).first()
    threshold = settings.low_balance_threshold if settings else 1.0
    
    if user.credits <= threshold and (not settings or settings.email_on_low_balance):
        send_email(
            user.email,
            "⚠️ Low Balance Alert - Namaskah SMS",
            f"""<h2>⚠️ Low Balance Alert</h2>
            <p>Your wallet balance is low: <strong>N{user.credits:.2f}</strong></p>
            <p>Fund your wallet to continue using Namaskah SMS.</p>
            <p><a href="{BASE_URL}/app">Fund Wallet Now</a></p>"""
        )
    
    # Create transaction
    transaction = Transaction(
        id=f"txn_{datetime.now(timezone.utc).timestamp()}",
        user_id=user.id,
        amount=-VERIFICATION_COST,
        type="debit",
        description=f"Verification for {req.service_name}"
    )
    db.add(transaction)
    
    # Check subscription for filtering permissions
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active"
    ).first()
    
    # Validate filtering permissions
    if req.area_code and subscription:
        plan = SUBSCRIPTION_PLANS[subscription.plan]
        if not plan['area_code']:
            raise HTTPException(status_code=403, detail="Area code selection requires Pro or Turbo plan")
    
    if req.carrier and subscription:
        plan = SUBSCRIPTION_PLANS[subscription.plan]
        if not plan['carrier']:
            raise HTTPException(status_code=403, detail="Carrier selection requires Turbo plan")
    
    # Create verification with filters
    verification_id = tv_client.create_verification(
        req.service_name, 
        req.capability,
        area_code=req.area_code,
        carrier=req.carrier
    )
    details = tv_client.get_verification(verification_id)
    
    verification = Verification(
        id=verification_id,
        user_id=user.id,
        service_name=req.service_name,
        phone_number=details.get("number"),
        capability=req.capability,
        status="pending",
        cost=cost
    )
    db.add(verification)
    db.commit()
    
    return {
        "id": verification.id,
        "service_name": verification.service_name,
        "phone_number": verification.phone_number,
        "capability": verification.capability,
        "status": verification.status,
        "cost": verification.cost,
        "remaining_credits": user.credits
    }

@app.get("/verify/{verification_id}", tags=["Verification"], summary="Get Verification Status")
def get_verification(verification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get verification details and current status"""
    verification = db.query(Verification).filter(
        Verification.id == verification_id,
        Verification.user_id == user.id
    ).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    details = tv_client.get_verification(verification_id)
    verification.status = "completed" if details.get("state") == "verificationCompleted" else "pending"
    db.commit()
    
    return {
        "id": verification.id,
        "service_name": verification.service_name,
        "phone_number": verification.phone_number,
        "status": verification.status,
        "cost": verification.cost,
        "created_at": verification.created_at
    }

@app.get("/verify/{verification_id}/messages", tags=["Verification"], summary="Get SMS Messages")
async def get_messages(verification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve SMS messages for verification. Triggers webhooks if configured."""
    verification = db.query(Verification).filter(
        Verification.id == verification_id,
        Verification.user_id == user.id
    ).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    messages = tv_client.get_messages(verification_id)
    
    # Send to webhooks and email if messages exist
    if messages:
        await send_webhook(user.id, verification_id, messages, db)
        
        # Send email notification
        settings = db.query(NotificationSettings).filter(NotificationSettings.user_id == user.id).first()
        if not settings or settings.email_on_sms:
            send_email(
                user.email,
                f"📨 SMS Received - {verification.service_name}",
                f"""<h2>🎉 SMS Code Received!</h2>
                <p>Your verification for <strong>{verification.service_name}</strong> has received an SMS.</p>
                <p><strong>Messages:</strong></p>
                <ul>{''.join([f'<li>{msg}</li>' for msg in messages])}</ul>
                <p>View in dashboard: <a href="{BASE_URL}/app">Namaskah SMS</a></p>"""
            )
    
    return {"verification_id": verification_id, "messages": messages}

@app.get("/verify/{verification_id}/voice", tags=["Verification"], summary="Get Voice Call Details")
def get_voice_call(verification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve voice call details including transcription and audio URL"""
    verification = db.query(Verification).filter(
        Verification.id == verification_id,
        Verification.user_id == user.id,
        Verification.capability == "voice"
    ).first()
    
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
        "received_at": verification.completed_at.isoformat() if verification.completed_at else None
    }

@app.delete("/verify/{verification_id}", tags=["Verification"], summary="Cancel Verification")
def cancel_verification(verification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Cancel active verification and refund credits to wallet"""
    # Strict user ownership check
    verification = db.query(Verification).filter(
        Verification.id == verification_id,
        Verification.user_id == user.id
    ).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found or not owned by you")
    
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
        description=f"Refund for cancelled {verification.service_name} verification"
    )
    db.add(transaction)
    
    verification.status = "cancelled"
    db.commit()
    
    # Refresh user to get updated credits
    db.refresh(user)
    
    return {"message": "Verification cancelled and refunded", "refunded": verification.cost, "new_balance": user.credits}

# Admin Endpoints
@app.get("/admin/users", tags=["Admin"], summary="List All Users")
def get_all_users(
    search: str = None,
    page: int = 1,
    limit: int = 50,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all registered users with search and pagination (admin only)"""
    query = db.query(User)
    
    # Search filter
    if search:
        query = query.filter(
            (User.email.contains(search)) | (User.id.contains(search))
        )
    
    # Get total count
    total = query.count()
    
    # Pagination
    offset = (page - 1) * limit
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "credits": u.credits,
                "free_verifications": u.free_verifications,
                "is_admin": u.is_admin,
                "email_verified": u.email_verified,
                "created_at": u.created_at.isoformat()
            }
            for u in users
        ],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }

@app.get("/admin/users/{user_id}/journey", tags=["Admin"], summary="Get User Journey")
def get_user_journey(user_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Get complete user journey with all activities"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all activities
    activities = db.query(ActivityLog).filter(
        ActivityLog.user_id == user_id
    ).order_by(ActivityLog.created_at.asc()).all()
    
    # Get payment logs
    payments = db.query(PaymentLog).filter(
        PaymentLog.user_id == user_id
    ).order_by(PaymentLog.created_at.asc()).all()
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat()
        },
        "activities": [
            {
                "timestamp": a.created_at.isoformat(),
                "page": a.page,
                "action": a.action,
                "element": a.element,
                "status": a.status,
                "details": a.details
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
                "credited": p.credited
            }
            for p in payments
        ]
    }

@app.get("/admin/users/{user_id}", tags=["Admin"], summary="Get User Details")
def get_user_details(user_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Get detailed user information including history (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get verification history
    verifications = db.query(Verification).filter(
        Verification.user_id == user_id
    ).order_by(Verification.created_at.desc()).limit(20).all()
    
    # Get transaction history
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).order_by(Transaction.created_at.desc()).limit(20).all()
    
    # Calculate stats
    from sqlalchemy import func
    total_spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "debit"
    ).scalar() or 0
    
    total_funded = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "credit"
    ).scalar() or 0
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "credits": user.credits,
            "free_verifications": user.free_verifications,
            "is_admin": user.is_admin,
            "email_verified": user.email_verified,
            "referral_code": user.referral_code,
            "created_at": user.created_at.isoformat()
        },
        "stats": {
            "total_verifications": len(verifications),
            "total_spent": abs(total_spent),
            "total_funded": total_funded
        },
        "recent_verifications": [
            {
                "id": v.id,
                "service_name": v.service_name,
                "status": v.status,
                "cost": v.cost,
                "created_at": v.created_at.isoformat()
            }
            for v in verifications
        ],
        "recent_transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "type": t.type,
                "description": t.description,
                "created_at": t.created_at.isoformat()
            }
            for t in transactions
        ]
    }

@app.get("/admin/export/users", tags=["Admin"], summary="Export Users to CSV")
def export_users_csv(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Export all users to CSV (admin only)"""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    users = db.query(User).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['ID', 'Email', 'Credits', 'Free Verifications', 'Is Admin', 'Email Verified', 'Created At'])
    
    # Data
    for u in users:
        writer.writerow([
            u.id,
            u.email,
            u.credits,
            u.free_verifications,
            u.is_admin,
            u.email_verified,
            u.created_at.isoformat()
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users_export.csv"}
    )

@app.get("/admin/export/transactions", tags=["Admin"], summary="Export Transactions to CSV")
def export_transactions_csv(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Export all transactions to CSV (admin only)"""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    transactions = db.query(Transaction).order_by(Transaction.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['ID', 'User ID', 'Amount', 'Type', 'Description', 'Created At'])
    
    # Data
    for t in transactions:
        writer.writerow([
            t.id,
            t.user_id,
            t.amount,
            t.type,
            t.description,
            t.created_at.isoformat()
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions_export.csv"}
    )

@app.post("/admin/credits/add", tags=["Admin"], summary="Add Credits to User")
def add_credits(req: AddCreditsRequest, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
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
        description=f"Admin added credits"
    )
    db.add(transaction)
    db.commit()
    
    return {"message": f"Added N{req.amount} credits", "new_balance": user.credits}

@app.get("/admin/analytics/summary", tags=["Admin"], summary="Get Analytics Summary")
def get_analytics_summary(email: str = None, days: int = 7, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Get analytics summary for user or all users"""
    from sqlalchemy import func
    from datetime import timedelta
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    query = db.query(ActivityLog).filter(ActivityLog.created_at >= start_date)
    if email:
        query = query.filter(ActivityLog.email == email)
    
    # Page views
    page_views = db.query(
        ActivityLog.page,
        func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.created_at >= start_date,
        ActivityLog.action == 'page_view'
    )
    if email:
        page_views = page_views.filter(ActivityLog.email == email)
    page_views = page_views.group_by(ActivityLog.page).all()
    
    # Button clicks
    button_clicks = db.query(
        ActivityLog.element,
        ActivityLog.page,
        func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.created_at >= start_date,
        ActivityLog.action == 'click'
    )
    if email:
        button_clicks = button_clicks.filter(ActivityLog.email == email)
    button_clicks = button_clicks.group_by(ActivityLog.element, ActivityLog.page).all()
    
    # Total activities
    total_activities = query.count()
    
    # Unique sessions
        ActivityLog.created_at >= start_date
    )
    if email:
        unique_sessions = unique_sessions.filter(ActivityLog.email == email)
    unique_sessions = unique_sessions.scalar() or 0
    
    return {
        "total_activities": total_activities,
        "unique_sessions": unique_sessions,
        "page_views": [
            {"page": p[0], "count": p[1]}
            for p in page_views
        ],
        "button_clicks": [
            {"element": b[0], "page": b[1], "count": b[2]}
            for b in button_clicks
        ]
    }

@app.get("/admin/payment-logs", tags=["Admin"], summary="Get Payment Logs")
def get_payment_logs(email: str = None, reference: str = None, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
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
                "updated_at": log.updated_at.isoformat() if log.updated_at else None
            }
            for log in logs
        ]
    }

@app.get("/admin/activity-logs", tags=["Admin"], summary="Get Activity Logs")
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
                "created_at": log.created_at.isoformat() if log.created_at else None
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
            user_agent=user_agent
        )
        
        return {"status": "tracked"}
    except Exception as e:
        print(f"Track error: {e}")
        return {"status": "error"}

@app.get("/subscription/plans", tags=["Subscription"], summary="Get Available Plans")
def get_subscription_plans():
    """Get all available subscription plans"""
    return {
        "plans": [
            {
                "id": "starter",
                "name": "Starter",
                "duration": "7 days",
                "price": 12.5,
                "price_usd": 25,
                "discount": "0%",
                "features": [
                    "Random phone numbers",
                    "Random carriers",
                    "7 days access",
                    "Basic support"
                ]
            },
            {
                "id": "pro",
                "name": "Pro",
                "duration": "30 days",
                "price": 25.0,
                "price_usd": 50,
                "discount": "20%",
                "features": [
                    "Choose area code",
                    "20% discount on all verifications",
                    "30 days access",
                    "Priority support",
                    "API access"
                ]
            },
            {
                "id": "turbo",
                "name": "Turbo",
                "duration": "Lifetime",
                "price": 75.0,
                "price_usd": 150,
                "discount": "35%",
                "features": [
                    "Choose area code",
                    "Choose carrier (Verizon, AT&T, T-Mobile)",
                    "35% discount on all verifications",
                    "Lifetime access",
                    "Premium support",
                    "Advanced API access"
                ]
            }
        ]
    }

@app.post("/subscription/subscribe", tags=["Subscription"], summary="Subscribe to Plan")
def subscribe_to_plan(req: SubscribeRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Subscribe to Pro or Turbo plan"""
    if req.plan not in ['pro', 'turbo']:
        raise HTTPException(status_code=400, detail="Invalid plan. Choose 'pro' or 'turbo'")
    
    plan = SUBSCRIPTION_PLANS[req.plan]
    
    # Check if user has enough credits
    if user.credits < plan['price']:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need N{plan['price']}, have N{user.credits}")
    
    # Check existing subscription
    existing = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    
    if existing:
        # Upgrade/downgrade
        existing.plan = req.plan
        existing.price = plan['price']
        existing.discount = plan['discount']
        existing.duration = plan['duration']
        existing.status = "active"
        existing.expires_at = None if plan['duration'] == 0 else datetime.now(timezone.utc) + timedelta(days=plan['duration'])
        existing.updated_at = datetime.now(timezone.utc)
    else:
        # New subscription
        subscription = Subscription(
            id=f"sub_{datetime.now(timezone.utc).timestamp()}",
            user_id=user.id,
            plan=req.plan,
            price=plan['price'],
            discount=plan['discount'],
            duration=plan['duration'],
            status="active",
            expires_at=None if plan['duration'] == 0 else datetime.now(timezone.utc) + timedelta(days=plan['duration'])
        )
        db.add(subscription)
    
    # Deduct first month payment
    user.credits -= plan['price']
    
    # Create transaction
    db.add(Transaction(
        id=f"txn_{datetime.now(timezone.utc).timestamp()}",
        user_id=user.id,
        amount=-plan['price'],
        type="debit",
        description=f"Subscription: {plan['name']} plan (monthly)"
    ))
    
    db.commit()
    
    expires_at = None if plan['duration'] == 0 else datetime.now(timezone.utc) + timedelta(days=plan['duration'])
    
    return {
        "message": f"Successfully subscribed to {plan['name']} plan!",
        "plan": req.plan,
        "duration": f"{plan['duration']} days" if plan['duration'] > 0 else "Lifetime",
        "expires_at": expires_at.isoformat() if expires_at else "Never",
        "remaining_credits": user.credits
    }

@app.get("/subscription/current", tags=["Subscription"], summary="Get Current Subscription")
def get_current_subscription(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's current subscription"""
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    
    if not subscription:
        return {
            "plan": "starter",
            "name": "Starter",
            "status": "active",
            "features": SUBSCRIPTION_PLANS['starter']
        }
    
    return {
        "plan": subscription.plan,
        "name": SUBSCRIPTION_PLANS[subscription.plan]['name'],
        "status": subscription.status,
        "price": subscription.price,
        "discount": f"{int(subscription.discount * 100)}%",
        "duration": f"{subscription.duration} days" if subscription.duration > 0 else "Lifetime",
        "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else "Never",
        "features": SUBSCRIPTION_PLANS[subscription.plan]
    }

@app.post("/subscription/cancel", tags=["Subscription"], summary="Cancel Subscription")
def cancel_subscription(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Cancel active subscription"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    subscription.status = "cancelled"
    subscription.cancelled_at = datetime.now(timezone.utc)
    db.commit()
    
    return {
        "message": "Subscription cancelled. You'll be downgraded to Starter plan when it expires.",
        "plan": subscription.plan,
        "active_until": subscription.expires_at.isoformat() if subscription.expires_at else "Lifetime (no refund)"
    }

@app.get("/admin/stats", tags=["Admin"], summary="Get Platform Statistics")
def get_stats(period: str = "30", admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Get platform-wide statistics (admin only)
    
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
    active_users = db.query(Verification.user_id).filter(
        Verification.created_at >= start_date
    ).distinct().count()
    
    # Verifications in period
    total_verifications = db.query(Verification).filter(
        Verification.created_at >= start_date
    ).count()
    
    # Revenue in period (sum of all debit transactions)
    total_revenue = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == "debit",
        Transaction.created_at >= start_date
    ).scalar() or 0
    total_revenue = abs(total_revenue)
    
    # Plan distribution (based on total funded amount)
    users_with_funding = db.query(
        User.id,
        func.sum(Transaction.amount).label('total_funded')
    ).join(Transaction, User.id == Transaction.user_id).filter(
        Transaction.type == "credit",
        Transaction.description.contains("funded")
    ).group_by(User.id).all()
    
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
    popular_services = db.query(
        Verification.service_name,
        func.count(Verification.id).label('count'),
        func.sum(Verification.cost).label('revenue')
    ).filter(
        Verification.created_at >= start_date
    ).group_by(
        Verification.service_name
    ).order_by(
        func.count(Verification.id).desc()
    ).limit(10).all()
    
    return {
        "total_users": total_users,
        "new_users": new_users,
        "active_users": active_users,
        "total_verifications": total_verifications,
        "total_revenue": total_revenue,
        "plan_distribution": {
            "pay_as_you_go": pay_as_you_go,
            "developer": developer,
            "enterprise": enterprise
        },
        "popular_services": [
            {
                "service": s[0],
                "count": s[1],
                "revenue": float(s[2] or 0)
            }
            for s in popular_services
        ]
    }

# Payment Endpoints
# REMOVED: Mock fund_wallet endpoint - Use Paystack only

@app.post("/wallet/paystack/initialize", tags=["Wallet"], summary="Initialize Paystack Payment")
def initialize_paystack(req: FundWalletRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Initialize Paystack payment with detailed transaction info"""
    if req.amount < 5:
        raise HTTPException(status_code=400, detail="Minimum funding amount is $5 USD")
    
    # Only Paystack is supported
    if req.payment_method != 'paystack':
        raise HTTPException(status_code=400, detail="Only Paystack payment is supported. Crypto payments are not available.")
    
    reference = f"namaskah_{user.id}_{int(datetime.now(timezone.utc).timestamp())}"
    amount_usd = req.amount  # User enters USD amount directly
    
    # Get current USD to NGN exchange rate (cached, updates hourly)
    USD_TO_NGN_RATE = get_usd_to_ngn_rate()
    amount_ngn = amount_usd * USD_TO_NGN_RATE  # Exact NGN amount based on current rate
    namaskah_amount = amount_usd * USD_TO_NAMASKAH
    
    if not PAYSTACK_SECRET_KEY or not PAYSTACK_SECRET_KEY.startswith('sk_'):
        raise HTTPException(status_code=503, detail="Payment system not configured. Please contact support.")
    
    try:
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
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
                "usd_amount": amount_usd
            },
            "channels": ["card", "bank", "ussd", "qr", "mobile_money", "bank_transfer"]
        }
        r = requests.post("https://api.paystack.co/transaction/initialize", 
                        json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        
        # Log payment initialization
        log_payment(db, user_id=user.id, email=user.email, reference=reference, 
                   amount_ngn=amount_ngn, amount_usd=amount_usd, namaskah_amount=namaskah_amount,
                   status="initialized")
        log_activity(db, user_id=user.id, email=user.email, action="payment_init", 
                    status="success", details=f"Paystack payment initialized: {reference}")
        
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
                "exchange_rate": "1N = $2 USD"
            },
            "payment_methods": ["Card", "Bank Transfer", "USSD", "QR Code", "Mobile Money"],
            "message": f"Pay NGN {amount_ngn:,.2f} (${amount_usd:.2f} USD)"
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Payment gateway error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment initialization failed: {str(e)}")

@app.post("/wallet/paystack/webhook", tags=["Wallet"], summary="Paystack Webhook")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Paystack payment webhooks with signature verification"""
    import hmac
    import hashlib
    
    # Get signature and body
    signature = request.headers.get('x-paystack-signature')
    body = await request.body()
    
    # Verify webhook signature (CRITICAL SECURITY)
    if not PAYSTACK_SECRET_KEY or not PAYSTACK_SECRET_KEY.startswith('sk_'):
        # Log but don't process if no valid secret key
        print("⚠️ Paystack webhook received but no valid secret key configured")
        return {"status": "ignored", "reason": "no_secret_key"}
    
    expected_signature = hmac.new(
        PAYSTACK_SECRET_KEY.encode('utf-8'),
        body,
        hashlib.sha512
    ).hexdigest()
    
    if signature != expected_signature:
        print(f"❌ Invalid Paystack signature: {signature[:20]}...")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Parse webhook data
    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    event = data.get('event')
    print(f"📥 Paystack webhook: {event}")
    
    if event == 'charge.success':
        payment_data = data.get('data', {})
        reference = payment_data.get('reference')
        amount_kobo = payment_data.get('amount', 0)
        amount = amount_kobo / 100  # Convert from kobo to Naira
        user_id = payment_data.get('metadata', {}).get('user_id')
        user_email = payment_data.get('metadata', {}).get('user_email') or payment_data.get('customer', {}).get('email')
        
        if not reference or not user_id:
            print(f"⚠️ Missing reference or user_id in webhook")
            # Log failed webhook
            if user_email:
                log_activity(db, email=user_email, action="webhook_received", status="failed", 
                           error="Missing reference or user_id")
            return {"status": "error", "reason": "missing_data"}
        
        # Check for duplicate transaction
        existing = db.query(Transaction).filter(
            Transaction.description.contains(reference)
        ).first()
        
        if existing:
            print(f"⚠️ Duplicate transaction: {reference}")
            # Update payment log
            payment_log = db.query(PaymentLog).filter(PaymentLog.reference == reference).first()
            if payment_log:
                payment_log.webhook_received = True
                payment_log.status = "duplicate"
                db.commit()
            return {"status": "duplicate", "reference": reference}
        
        # Find user and add credits
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"❌ User not found: {user_id}")
            log_activity(db, user_id=user_id, email=user_email, action="webhook_received", 
                        status="failed", error=f"User not found: {user_id}")
            return {"status": "error", "reason": "user_not_found"}
        
        # Convert NGN to Namaskah coins
        # Get USD amount from metadata or calculate from NGN
        usd_amount = payment_data.get('metadata', {}).get('usd_amount', amount / get_usd_to_ngn_rate())
        namaskah_amount = usd_amount * USD_TO_NAMASKAH
        
        user.credits += namaskah_amount
        
        # Create transaction
        transaction = Transaction(
            id=f"txn_{datetime.now(timezone.utc).timestamp()}",
            user_id=user.id,
            amount=namaskah_amount,
            type="credit",
            description=f"Paystack payment: {reference} (NGN {amount})"
        )
        db.add(transaction)
        
        # Update payment log
        payment_log = db.query(PaymentLog).filter(PaymentLog.reference == reference).first()
        if payment_log:
            payment_log.webhook_received = True
            payment_log.credited = True
            payment_log.status = "completed"
            payment_log.updated_at = datetime.now(timezone.utc)
        else:
            # Create payment log if doesn't exist
            log_payment(db, user_id=user.id, email=user.email, reference=reference,
                       amount_ngn=amount, amount_usd=usd_amount, namaskah_amount=namaskah_amount,
                       status="completed", webhook_received=True, credited=True)
        
        # Log activity
        log_activity(db, user_id=user.id, email=user.email, action="payment_completed", 
                    status="success", details=f"Credited N{namaskah_amount:.2f} from {reference}")
        
        db.commit()
        
        print(f"✅ Payment processed: {reference} - N{namaskah_amount} for {user.email}")
        
        # Send confirmation email
        send_email(
            user.email,
            "💰 Payment Successful - Namaskah SMS",
            f"""<h2>Payment Confirmed!</h2>
            <p>Your payment of <strong>NGN {amount:.2f}</strong> has been received.</p>
            <p>Credited: <strong>N{namaskah_amount:.2f}</strong></p>
            <p>New balance: <strong>N{user.credits:.2f}</strong></p>
            <p>Reference: {reference}</p>
            <p><a href="{BASE_URL}/app">Start Using Credits</a></p>"""
        )
        
        return {"status": "success", "reference": reference, "amount": namaskah_amount}
    
    elif event == 'charge.failed':
        payment_data = data.get('data', {})
        reference = payment_data.get('reference')
        print(f"❌ Payment failed: {reference}")
        return {"status": "failed", "reference": reference}
    
    return {"status": "ignored", "event": event}

@app.get("/wallet/paystack/verify/{reference}", tags=["Wallet"], summary="Verify Payment")
def verify_payment(reference: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Verify Paystack payment status (manual verification)"""
    if not PAYSTACK_SECRET_KEY or not PAYSTACK_SECRET_KEY.startswith('sk_'):
        return {"status": "demo", "message": "Demo mode - payment not verified"}
    
    try:
        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        r = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
        r.raise_for_status()
        response_data = r.json()
        
        if not response_data.get('status'):
            return {"status": "error", "message": "Invalid response from Paystack"}
        
        payment_data = response_data.get('data', {})
        payment_status = payment_data.get('status')
        
        if payment_status == 'success':
            amount_kobo = payment_data.get('amount', 0)
            amount = amount_kobo / 100  # Convert from kobo
            
            # Check if already credited
            existing = db.query(Transaction).filter(
                Transaction.description.contains(reference)
            ).first()
            
            if existing:
                return {
                    "status": "already_credited",
                    "message": "Payment already processed",
                    "reference": reference,
                    "balance": user.credits
                }
            
            # Convert USD to Namaskah coins
            namaskah_amount = amount * USD_TO_NAMASKAH
            
            user.credits += namaskah_amount
            transaction = Transaction(
                id=f"txn_{datetime.now(timezone.utc).timestamp()}",
                user_id=user.id,
                amount=namaskah_amount,
                type="credit",
                description=f"Paystack payment verified: {reference} (NGN {amount})"
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
                <p>Reference: {reference}</p>"""
            )
            
            return {
                "status": "success",
                "amount": namaskah_amount,
                "new_balance": user.credits,
                "reference": reference,
                "message": f"Credited N{namaskah_amount:.2f} to your wallet"
            }
        else:
            return {
                "status": "failed",
                "message": f"Payment status: {payment_status}",
                "reference": reference
            }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Paystack API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")

# REMOVED: Crypto payment endpoints - Not implemented

# API Key Endpoints
@app.post("/api-keys/create", tags=["API Keys"], summary="Create API Key")
def create_api_key(req: CreateAPIKeyRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate new API key for programmatic access"""
    import secrets
    key = f"nsk_{secrets.token_urlsafe(32)}"
    
    api_key = APIKey(
        id=f"key_{datetime.now(timezone.utc).timestamp()}",
        user_id=user.id,
        key=key,
        name=req.name
    )
    db.add(api_key)
    db.commit()
    
    return {"key": key, "name": req.name, "created_at": api_key.created_at}

@app.get("/api-keys/list", tags=["API Keys"], summary="List API Keys")
def list_api_keys(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all API keys for current user"""
    keys = db.query(APIKey).filter(APIKey.user_id == user.id).all()
    return {
        "keys": [
            {
                "id": k.id,
                "name": k.name,
                "key": k.key[:12] + "...",
                "is_active": k.is_active,
                "created_at": k.created_at
            }
            for k in keys
        ]
    }

@app.delete("/api-keys/{key_id}", tags=["API Keys"], summary="Delete API Key")
def delete_api_key(key_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revoke API key permanently"""
    key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(key)
    db.commit()
    return {"message": "API key deleted"}

# Webhook Endpoints
@app.post("/webhooks/create", tags=["Webhooks"], summary="Create Webhook")
def create_webhook(req: CreateWebhookRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Register webhook URL for SMS notifications"""
    webhook = Webhook(
        id=f"webhook_{datetime.now(timezone.utc).timestamp()}",
        user_id=user.id,
        url=req.url
    )
    db.add(webhook)
    db.commit()
    
    return {"id": webhook.id, "url": webhook.url, "is_active": webhook.is_active}

@app.get("/webhooks/list", tags=["Webhooks"], summary="List Webhooks")
def list_webhooks(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all configured webhooks"""
    webhooks = db.query(Webhook).filter(Webhook.user_id == user.id).all()
    return {
        "webhooks": [
            {
                "id": w.id,
                "url": w.url,
                "is_active": w.is_active,
                "created_at": w.created_at
            }
            for w in webhooks
        ]
    }

@app.delete("/webhooks/{webhook_id}", tags=["Webhooks"], summary="Delete Webhook")
def delete_webhook(webhook_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Remove webhook configuration"""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id, Webhook.user_id == user.id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    db.delete(webhook)
    db.commit()
    return {"message": "Webhook deleted"}

async def send_webhook(user_id: str, verification_id: str, messages: list, db: Session):
    """Send SMS to user webhooks"""
    webhooks = db.query(Webhook).filter(Webhook.user_id == user_id, Webhook.is_active == True).all()
    
    for webhook in webhooks:
        try:
            payload = {
                "verification_id": verification_id,
                "messages": messages,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            requests.post(webhook.url, json=payload, timeout=5)
        except:
            pass

# Analytics Endpoints
@app.get("/analytics/dashboard", tags=["Analytics"], summary="Get Analytics Dashboard")
def get_analytics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get usage analytics: total verifications, spending, success rate, popular services, daily usage"""
    from sqlalchemy import func
    
    # Total verifications
    total_verifications = db.query(Verification).filter(Verification.user_id == user.id).count()
    
    # Total spent
    total_spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id,
        Transaction.type == "debit"
    ).scalar() or 0
    
    # Success rate
    completed = db.query(Verification).filter(
        Verification.user_id == user.id,
        Verification.status == "completed"
    ).count()
    success_rate = (completed / total_verifications * 100) if total_verifications > 0 else 0
    
    # Popular services
    popular = db.query(
        Verification.service_name,
        func.count(Verification.id).label('count')
    ).filter(
        Verification.user_id == user.id
    ).group_by(Verification.service_name).order_by(func.count(Verification.id).desc()).limit(5).all()
    
    # Recent activity (last 7 days)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_verifications = db.query(Verification).filter(
        Verification.user_id == user.id,
        Verification.created_at >= seven_days_ago
    ).count()
    
    # Daily usage (last 7 days)
    daily_usage = []
    for i in range(7):
        day = datetime.now(timezone.utc) - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        count = db.query(Verification).filter(
            Verification.user_id == user.id,
            Verification.created_at >= day_start,
            Verification.created_at < day_end
        ).count()
        
        daily_usage.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": count
        })
    
    return {
        "total_verifications": total_verifications,
        "total_spent": abs(total_spent),
        "success_rate": round(success_rate, 1),
        "popular_services": [{"service": s[0], "count": s[1]} for s in popular],
        "recent_verifications": recent_verifications,
        "daily_usage": list(reversed(daily_usage))
    }

# Notification Settings Endpoints
@app.get("/notifications/settings", tags=["Notifications"], summary="Get Notification Settings")
def get_notification_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get email notification preferences"""
    settings = db.query(NotificationSettings).filter(NotificationSettings.user_id == user.id).first()
    
    if not settings:
        settings = NotificationSettings(
            id=f"notif_{datetime.now(timezone.utc).timestamp()}",
            user_id=user.id
        )
        db.add(settings)
        db.commit()
    
    return {
        "email_on_sms": settings.email_on_sms,
        "email_on_low_balance": settings.email_on_low_balance,
        "low_balance_threshold": settings.low_balance_threshold
    }

@app.post("/notifications/settings", tags=["Notifications"], summary="Update Notification Settings")
def update_notification_settings(email_on_sms: bool = True, email_on_low_balance: bool = True, 
                                low_balance_threshold: float = 1.0,
                                user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Configure email notification preferences"""
    settings = db.query(NotificationSettings).filter(NotificationSettings.user_id == user.id).first()
    
    if not settings:
        settings = NotificationSettings(
            id=f"notif_{datetime.now(timezone.utc).timestamp()}",
            user_id=user.id
        )
        db.add(settings)
    
    settings.email_on_sms = email_on_sms
    settings.email_on_low_balance = email_on_low_balance
    settings.low_balance_threshold = low_balance_threshold
    db.commit()
    
    return {"message": "Settings updated"}

# Referral Endpoints
@app.get("/referrals/stats", tags=["Referrals"], summary="Get Referral Statistics")
def get_referral_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get referral code, earnings, and referred users list"""
    referrals = db.query(Referral).filter(Referral.referrer_id == user.id).all()
    
    referred_users = []
    for ref in referrals:
        referred_user = db.query(User).filter(User.id == ref.referred_id).first()
        if referred_user:
            referred_users.append({
                "email": referred_user.email,
                "joined_at": ref.created_at,
                "reward": ref.reward_amount
            })
    
    return {
        "referral_code": user.referral_code,
        "total_referrals": len(referrals),
        "total_earnings": user.referral_earnings,
        "referral_link": f"{BASE_URL}/app?ref={user.referral_code}",
        "referred_users": referred_users
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
        status="open"
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
        <p>You'll receive a response at this email address.</p>"""
    )
    
    return {
        "success": True,
        "ticket_id": ticket.id,
        "message": "Support request submitted successfully. We'll respond within 24 hours."
    }

@app.get("/admin/support/tickets", tags=["Admin"], summary="Get All Support Tickets")
def get_support_tickets(status: str = None, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
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
                "updated_at": t.updated_at
            }
            for t in tickets
        ]
    }

@app.post("/admin/support/{ticket_id}/respond", tags=["Admin"], summary="Respond to Support Ticket")
def respond_to_ticket(ticket_id: str, req: AdminResponseRequest, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
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
        <p>Best regards,<br>Namaskah Support Team</p>"""
    )
    
    return {"message": "Response sent successfully", "ticket_id": ticket.id}

@app.patch("/admin/support/{ticket_id}/status", tags=["Admin"], summary="Update Ticket Status")
def update_ticket_status(ticket_id: str, status: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Update support ticket status (admin only)."""
    valid_statuses = ["open", "in_progress", "resolved", "closed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.status = status
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    return {"message": "Status updated", "ticket_id": ticket.id, "new_status": status}

# Rental Pricing (in Namaskah coins N)
# Service-Specific Rentals (for single service like WhatsApp)
RENTAL_SERVICE_SPECIFIC = {
    168: 5.0,      # 7 days
    336: 9.0,      # 14 days
    720: 16.0,     # 30 days
    1440: 28.0,    # 60 days
    2160: 38.0,    # 90 days
    8760: 50.0     # 365 days
}

# General Use Rentals (can receive from any service)
RENTAL_GENERAL_USE = {
    168: 6.0,      # 7 days
    336: 11.0,     # 14 days
    720: 20.0,     # 30 days
    1440: 35.0,    # 60 days
    2160: 48.0,    # 90 days
    8760: 80.0     # 365 days
}

# Rental modes
RENTAL_MODES = {
    'always_active': 1.0,   # Full price - always active
    'manual': 0.7           # 30% discount - needs activation
}

def calculate_rental_cost(hours: float, service_name: str = 'general', mode: str = 'always_active') -> float:
    """Calculate rental cost based on duration, service, and mode (in N)"""
    # Minimum 7 days (168 hours)
    if hours < 168:
        hours = 168
    
    # Determine if service-specific or general use
    is_general = service_name.lower() in ['general', 'unlisted', 'any']
    pricing_table = RENTAL_GENERAL_USE if is_general else RENTAL_SERVICE_SPECIFIC
    
    # Get base price
    if hours in pricing_table:
        base_cost = pricing_table[hours]
    else:
        # Calculate proportional cost based on 7-day rate
        base_cost = round((hours / 168) * pricing_table[168], 2)
    
    # Apply mode discount
    mode_multiplier = RENTAL_MODES.get(mode, RENTAL_MODES['always_active'])
    
    return round(base_cost * mode_multiplier, 2)

def calculate_refund(rental: NumberRental) -> float:
    """Calculate refund for early release (50% of unused time, min 1hr used)"""
    used_hours = (datetime.now(timezone.utc) - rental.started_at).total_seconds() / 3600
    if used_hours < 1:
        used_hours = 1
    unused_hours = max(0, rental.duration_hours - used_hours)
    hourly_rate = rental.cost / rental.duration_hours
    return round((unused_hours * hourly_rate) * 0.5, 2)

# Rental Endpoints
@app.post("/rentals/create", tags=["Rentals"], summary="Create Number Rental")
def create_rental(req: CreateRentalRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Rent a phone number for specified duration
    
    Minimum 7 days. Pricing varies by service and mode (Always Ready vs Manual).
    """
    # Email verification required for rentals
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Email verification required for number rentals. Please verify your email first.")
    
    # Default to always_active mode if not specified
    mode = getattr(req, 'mode', 'always_active')
    cost = calculate_rental_cost(req.duration_hours, req.service_name, mode)
    
    if user.credits < cost:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need N{cost}, have N{user.credits}")
    
    # Check active rental limit (max 5)
    active_count = db.query(NumberRental).filter(
        NumberRental.user_id == user.id,
        NumberRental.status == "active"
    ).count()
    if active_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 active rentals allowed")
    
    # Deduct credits
    user.credits -= cost
    
    # Check subscription for filtering permissions
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active"
    ).first()
    
    # Validate filtering permissions
    if req.area_code and subscription:
        plan = SUBSCRIPTION_PLANS[subscription.plan]
        if not plan['area_code']:
            raise HTTPException(status_code=403, detail="Area code selection requires Pro or Turbo plan")
    
    if req.carrier and subscription:
        plan = SUBSCRIPTION_PLANS[subscription.plan]
        if not plan['carrier']:
            raise HTTPException(status_code=403, detail="Carrier selection requires Turbo plan")
    
    # Create verification for rental
    try:
        verification_id = tv_client.create_verification(
            req.service_name, 
            "sms",
            area_code=req.area_code,
            carrier=req.carrier
        )
        details = tv_client.get_verification(verification_id)
        phone_number = details.get("number")
        
        if not phone_number:
            raise HTTPException(status_code=503, detail="Failed to get phone number from provider")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Rental service unavailable: {str(e)}")
    
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
        auto_extend=req.auto_extend
    )
    db.add(rental)
    
    # Create transaction
    db.add(Transaction(
        id=f"txn_{now.timestamp()}",
        user_id=user.id,
        amount=-cost,
        type="debit",
        description=f"Rental: {req.service_name} for {req.duration_hours}h"
    ))
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
        "status": rental.status
    }

@app.get("/rentals/active", tags=["Rentals"], summary="List Active Rentals")
def list_active_rentals(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all active rentals for current user"""
    rentals = db.query(NumberRental).filter(
        NumberRental.user_id == user.id,
        NumberRental.status == "active"
    ).order_by(NumberRental.expires_at).all()
    
    now = datetime.now(timezone.utc)
    return {
        "rentals": [
            {
                "id": r.id,
                "phone_number": r.phone_number,
                "service_name": r.service_name,
                "expires_at": r.expires_at.isoformat(),
                "time_remaining_seconds": max(0, int((r.expires_at - now).total_seconds())),
                "auto_extend": r.auto_extend
            }
            for r in rentals
        ]
    }

@app.get("/rentals/{rental_id}", tags=["Rentals"], summary="Get Rental Details")
def get_rental(rental_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get rental status and details"""
    rental = db.query(NumberRental).filter(
        NumberRental.id == rental_id,
        NumberRental.user_id == user.id
    ).first()
    
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
        "time_remaining_seconds": max(0, int((rental.expires_at - now).total_seconds())),
        "duration_hours": rental.duration_hours,
        "cost": rental.cost,
        "auto_extend": rental.auto_extend
    }

@app.post("/rentals/{rental_id}/extend", tags=["Rentals"], summary="Extend Rental")
def extend_rental(rental_id: str, req: ExtendRentalRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Extend rental duration"""
    rental = db.query(NumberRental).filter(
        NumberRental.id == rental_id,
        NumberRental.user_id == user.id,
        NumberRental.status == "active"
    ).first()
    
    if not rental:
        raise HTTPException(status_code=404, detail="Active rental not found")
    
    mode = getattr(rental, 'mode', 'always_active')
    cost = calculate_rental_cost(req.additional_hours, rental.service_name, mode)
    
    if user.credits < cost:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need N{cost}, have N{user.credits}")
    
    user.credits -= cost
    rental.expires_at += timedelta(hours=req.additional_hours)
    rental.duration_hours += req.additional_hours
    rental.cost += cost
    
    db.add(Transaction(
        id=f"txn_{datetime.now(timezone.utc).timestamp()}",
        user_id=user.id,
        amount=-cost,
        type="debit",
        description=f"Extended rental {rental_id} by {req.additional_hours}h"
    ))
    db.commit()
    
    return {
        "id": rental.id,
        "new_expires_at": rental.expires_at.isoformat(),
        "cost": cost,
        "remaining_credits": user.credits
    }

@app.post("/rentals/{rental_id}/release", tags=["Rentals"], summary="Release Rental Early")
def release_rental(rental_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Release rental early and get 50% refund for unused time"""
    rental = db.query(NumberRental).filter(
        NumberRental.id == rental_id,
        NumberRental.user_id == user.id,
        NumberRental.status == "active"
    ).first()
    
    if not rental:
        raise HTTPException(status_code=404, detail="Active rental not found")
    
    refund = calculate_refund(rental)
    user.credits += refund
    rental.status = "released"
    rental.released_at = datetime.now(timezone.utc)
    
    if refund > 0:
        db.add(Transaction(
            id=f"txn_{datetime.now(timezone.utc).timestamp()}",
            user_id=user.id,
            amount=refund,
            type="credit",
            description=f"Refund for early release of rental {rental_id}"
        ))
    
    db.commit()
    
    return {
        "id": rental.id,
        "status": "released",
        "refund": refund,
        "remaining_credits": user.credits,
        "message": f"Refunded N{refund} for unused time"
    }

@app.get("/rentals/{rental_id}/messages", tags=["Rentals"], summary="Get Rental Messages")
def get_rental_messages(rental_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all SMS messages for rented number"""
    rental = db.query(NumberRental).filter(
        NumberRental.id == rental_id,
        NumberRental.user_id == user.id
    ).first()
    
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
            "message_count": len(messages)
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
            "error": str(e)
        }

# CORS for frontend
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import time

# Get allowed origins from environment
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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
    if request.url.scheme == "http" and request.url.hostname not in ["localhost", "127.0.0.1"]:
        url = request.url.replace(scheme="https")
        return RedirectResponse(url, status_code=301)
    return await call_next(request)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
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
    if request.url.path.startswith("/static") or request.url.path in ["/", "/app", "/admin", "/api-docs", "/health"]:
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
