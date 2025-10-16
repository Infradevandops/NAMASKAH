"""Namaskah SMS - With Pricing & Admin Panel"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

import jwt
from dotenv import load_dotenv
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Float

from sqlalchemy.orm import sessionmaker, Session
from passlib.hash import bcrypt
import requests

load_dotenv()

# Initialize Sentry for error tracking
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
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

# Pricing tiers (discounts applied to base price)
PRICING_TIERS = {
    'pay_as_you_go': 1.0,      # No discount
    'developer': 0.80,         # 20% discount
    'enterprise': 0.65         # 35% discount
}

# Minimum purchase amounts for discounted tiers (in N)
MIN_PURCHASE = {
    'developer': 25.0,    # N25 ($50 USD)
    'enterprise': 100.0   # N100 ($200 USD)
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

# Email Config
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@namaskah.app")

# Database
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
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

Base.metadata.create_all(bind=engine)

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

    def create_verification(self, service_name: str, capability: str = "sms"):
        headers = {"Authorization": f"Bearer {self.get_token()}"}
        r = requests.post(
            f"{self.base_url}/api/pub/v2/verifications",
            headers=headers,
            json={"serviceName": service_name, "capability": capability}
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
    version="2.1.0",
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
- **Symbol**: N (Namaskah Coin)
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

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

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

@app.get("/health", tags=["System"], summary="Health Check")
def health():
    return {
        "status": "healthy",
        "service": "namaskah-sms",
        "version": "2.0.0",
        "database": "connected",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

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
        
        # Get success rates per service
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
                if success_rate < 50:
                    status_map[stat.service_name] = 'down'
                    down_count += 1
                elif success_rate < 85:
                    status_map[stat.service_name] = 'degraded'
                    degraded_count += 1
                else:
                    status_map[stat.service_name] = 'operational'
        
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
            }
        }
    except Exception as e:
        # Default to all operational if error
        return {
            "categories": {},
            "status": {},
            "overall_status": "operational",
            "stats": {"down": 0, "degraded": 0, "operational": 0}
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
        password_hash=bcrypt.hash(req.password),
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
    
    # Send verification email
    verification_url = f"http://localhost:8000/auth/verify?token={verification_token}"
    send_email(
        user.email,
        "Verify Your Email - Namaskah SMS",
        f"""<h2>Welcome to Namaskah SMS!</h2>
        <p>Click the link below to verify your email:</p>
        <p><a href="{verification_url}">Verify Email</a></p>
        <p>Or copy this link: {verification_url}</p>
        <p>This link expires in 24 hours.</p>"""
    )
    
    token = jwt.encode({"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(days=30)}, JWT_SECRET)
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
                password_hash=bcrypt.hash(google_id),  # Use Google ID as password
                credits=0.0,
                free_verifications=1.0,
                referral_code=secrets.token_urlsafe(6)
            )
            db.add(user)
            db.commit()
        
        # Generate JWT
        token = jwt.encode(
            {"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(days=30)},
            JWT_SECRET
        )
        
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
        password_valid = bcrypt.verify(req.password, user.password_hash)
    except Exception as e:
        print(f"Password verify error: {e}")
        password_valid = False
    
    if not password_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = jwt.encode({"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(days=30)}, JWT_SECRET)
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
    
    verification_url = f"http://localhost:8000/auth/verify?token={verification_token}"
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
    
    reset_url = f"http://localhost:8000/auth/reset-password?token={reset_token}"
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
    
    user.password_hash = bcrypt.hash(req.new_password)
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
        "created_at": user.created_at
    }

@app.get("/verifications/history", tags=["Verification"], summary="Get Verification History")
def get_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get last 20 verifications for current user"""
    verifications = db.query(Verification).filter(
        Verification.user_id == user.id
    ).order_by(Verification.created_at.desc()).limit(20).all()
    
    return {
        "verifications": [
            {
                "id": v.id,
                "service_name": v.service_name,
                "phone_number": v.phone_number,
                "status": v.status,
                "cost": v.cost,
                "created_at": v.created_at
            }
            for v in verifications
        ]
    }

@app.get("/transactions/history", tags=["Wallet"], summary="Get Transaction History")
def get_transactions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get last 50 transactions (credits/debits) for current user"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user.id
    ).order_by(Transaction.created_at.desc()).limit(50).all()
    
    return {
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "type": t.type,
                "description": t.description,
                "created_at": t.created_at
            }
            for t in transactions
        ]
    }

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
    
    # Determine pricing tier based on user's total funded amount
    total_funded = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.type == "credit",
        Transaction.description.contains("funded")
    ).with_entities(Transaction.amount).all()
    total_funded_amount = sum([t[0] for t in total_funded]) if total_funded else 0
    
    # Apply tier discount
    if total_funded_amount >= MIN_PURCHASE['enterprise']:
        tier_multiplier = PRICING_TIERS['enterprise']
    elif total_funded_amount >= MIN_PURCHASE['developer']:
        tier_multiplier = PRICING_TIERS['developer']
    else:
        tier_multiplier = PRICING_TIERS['pay_as_you_go']
    
    cost = round(base_cost * tier_multiplier, 2)
    
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
            <p><a href="http://localhost:8000/app">Fund Wallet Now</a></p>"""
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
    
    # Create verification
    verification_id = tv_client.create_verification(req.service_name, req.capability)
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
                <p>View in dashboard: <a href="http://localhost:8000/app">Namaskah SMS</a></p>"""
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
def get_all_users(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Get all registered users (admin only)"""
    users = db.query(User).all()
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "credits": u.credits,
                "is_admin": u.is_admin,
                "created_at": u.created_at
            }
            for u in users
        ]
    }

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
        "total_verifications": total_verifications,
        "total_revenue": total_revenue,
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
@app.post("/wallet/fund", tags=["Wallet"], summary="Fund Wallet")
def fund_wallet(req: FundWalletRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Add credits to wallet. Minimum N2.50 ($5 USD). Supports Paystack, Bitcoin, Ethereum, Solana, USDT."""
    if req.amount < 2.5:
        raise HTTPException(status_code=400, detail="Minimum funding amount is N2.50 ($5 USD)")
    
    payment_methods = {
        'paystack': '🏦 Paystack',
        'bitcoin': '₿ Bitcoin',
        'ethereum': 'Ξ Ethereum',
        'solana': '◎ Solana',
        'usdt': '₮ USDT'
    }
    
    if req.payment_method not in payment_methods:
        raise HTTPException(status_code=400, detail="Invalid payment method")
    
    # Add credits (amount is in N)
    user.credits += req.amount
    
    # Create transaction
    transaction = Transaction(
        id=f"txn_{datetime.now(timezone.utc).timestamp()}",
        user_id=user.id,
        amount=req.amount,
        type="credit",
        description=f"Wallet funded via {payment_methods[req.payment_method]}"
    )
    db.add(transaction)
    
    # Check if user was referred and this is their first funding of N2.50+
    if req.amount >= 2.5 and user.referred_by:
        referrer = db.query(User).filter(User.id == user.referred_by).first()
        if referrer:
            # Check if referrer already got reward
            existing_reward = db.query(Transaction).filter(
                Transaction.user_id == referrer.id,
                Transaction.description.contains(f"Referral reward from {user.email}")
            ).first()
            
            if not existing_reward:
                referrer.free_verifications += 1
                referrer.referral_earnings += 1.0
                db.add(Transaction(
                    id=f"txn_{datetime.now(timezone.utc).timestamp() + 0.001}",
                    user_id=referrer.id,
                    amount=1.0,
                    type="credit",
                    description=f"Referral reward from {user.email} (1 free verification)"
                ))
    
    db.commit()
    
    return {
        "success": True,
        "amount": req.amount,
        "new_balance": user.credits,
        "payment_method": payment_methods[req.payment_method],
        "message": f"Successfully added N{req.amount:.2f} to your wallet"
    }

@app.post("/wallet/paystack/initialize", tags=["Wallet"], summary="Initialize Paystack Payment")
def initialize_paystack(req: FundWalletRequest, user: User = Depends(get_current_user)):
    """Initialize Paystack payment"""
    if req.amount < 2.5:
        raise HTTPException(status_code=400, detail="Minimum funding amount is N2.50 ($5 USD)")
    
    reference = f"namaskah_{user.id}_{int(datetime.now(timezone.utc).timestamp())}"
    
    if PAYSTACK_SECRET_KEY and PAYSTACK_SECRET_KEY.startswith('sk_'):
        # Real Paystack integration
        try:
            headers = {
                "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "email": user.email,
                "amount": int(req.amount * 100),  # Convert to kobo/cents
                "reference": reference,
                "callback_url": f"http://localhost:8000/app?reference={reference}",
                "metadata": {
                    "user_id": user.id,
                    "type": "wallet_funding"
                }
            }
            r = requests.post("https://api.paystack.co/transaction/initialize", 
                            json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            
            return {
                "authorization_url": data["data"]["authorization_url"],
                "reference": reference,
                "amount": req.amount
            }
        except Exception as e:
            print(f"Paystack error: {e}")
            # Fallback to demo mode
            pass
    
    # Demo mode
    return {
        "authorization_url": f"http://localhost:8000/app?payment=success&ref={reference}",
        "reference": reference,
        "amount": req.amount,
        "demo": True
    }

@app.post("/wallet/paystack/webhook", tags=["Wallet"], summary="Paystack Webhook")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Paystack payment webhooks"""
    import hmac
    import hashlib
    
    # Verify webhook signature
    signature = request.headers.get('x-paystack-signature')
    body = await request.body()
    
    if PAYSTACK_SECRET_KEY:
        expected_signature = hmac.new(
            PAYSTACK_SECRET_KEY.encode('utf-8'),
            body,
            hashlib.sha512
        ).hexdigest()
        
        if signature != expected_signature:
            raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Parse webhook data
    data = await request.json()
    event = data.get('event')
    
    if event == 'charge.success':
        payment_data = data['data']
        reference = payment_data['reference']
        amount = payment_data['amount'] / 100  # Convert from kobo
        user_id = payment_data['metadata'].get('user_id')
        
        # Find user and add credits
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.credits += amount
            
            # Create transaction
            db.add(Transaction(
                id=f"txn_{datetime.now(timezone.utc).timestamp()}",
                user_id=user.id,
                amount=amount,
                type="credit",
                description=f"Paystack payment: {reference}"
            ))
            db.commit()
            
            # Send confirmation email
            send_email(
                user.email,
                "💰 Payment Successful - Namaskah SMS",
                f"""<h2>Payment Confirmed!</h2>
                <p>Your payment of <strong>N{amount:.2f}</strong> has been received.</p>
                <p>New balance: <strong>N{user.credits:.2f}</strong></p>
                <p>Reference: {reference}</p>
                <p><a href="http://localhost:8000/app">Start Using Credits</a></p>"""
            )
    
    return {"status": "success"}

@app.get("/wallet/paystack/verify/{reference}", tags=["Wallet"], summary="Verify Payment")
def verify_payment(reference: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Verify Paystack payment status"""
    if not PAYSTACK_SECRET_KEY or not PAYSTACK_SECRET_KEY.startswith('sk_'):
        return {"status": "demo", "message": "Demo mode - payment not verified"}
    
    try:
        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        r = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
        r.raise_for_status()
        data = r.json()
        
        if data['data']['status'] == 'success':
            amount = data['data']['amount'] / 100
            
            # Check if already credited
            existing = db.query(Transaction).filter(
                Transaction.user_id == user.id,
                Transaction.description.contains(reference)
            ).first()
            
            if not existing:
                user.credits += amount
                db.add(Transaction(
                    id=f"txn_{datetime.now(timezone.utc).timestamp()}",
                    user_id=user.id,
                    amount=amount,
                    type="credit",
                    description=f"Paystack payment: {reference}"
                ))
                db.commit()
            
            return {
                "status": "success",
                "amount": amount,
                "new_balance": user.credits,
                "reference": reference
            }
        else:
            return {"status": "failed", "message": "Payment not successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/wallet/crypto/address", tags=["Wallet"], summary="Get Crypto Payment Address")
def get_crypto_address(req: FundWalletRequest, user: User = Depends(get_current_user)):
    """Get crypto payment address"""
    if req.amount < 2.5:
        raise HTTPException(status_code=400, detail="Minimum funding amount is N2.50 ($5 USD)")
    
    addresses = {
        'bitcoin': BITCOIN_ADDRESS,
        'ethereum': ETHEREUM_ADDRESS,
        'solana': SOLANA_ADDRESS,
        'usdt': USDT_ADDRESS
    }
    
    if req.payment_method not in addresses:
        raise HTTPException(status_code=400, detail="Invalid crypto method")
    
    address = addresses[req.payment_method]
    payment_id = f"crypto_{user.id}_{int(datetime.now(timezone.utc).timestamp())}"
    
    return {
        "address": address,
        "amount": req.amount,
        "currency": req.payment_method.upper(),
        "payment_id": payment_id,
        "qr_code": f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={address}",
        "explorer_url": get_explorer_url(req.payment_method, address),
        "instructions": f"Send exactly N{req.amount} (${req.amount * NAMASKAH_TO_USD} USD) worth of {req.payment_method.upper()} to the address above"
    }

def get_explorer_url(crypto: str, address: str) -> str:
    explorers = {
        'bitcoin': f'https://blockchair.com/bitcoin/address/{address}',
        'ethereum': f'https://etherscan.io/address/{address}',
        'solana': f'https://explorer.solana.com/address/{address}',
        'usdt': f'https://etherscan.io/address/{address}'
    }
    return explorers.get(crypto, '')

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
        "referral_link": f"http://localhost:8000/app?ref={user.referral_code}",
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
    
    # Create verification for rental
    verification_id = tv_client.create_verification(req.service_name, "sms")
    details = tv_client.get_verification(verification_id)
    
    now = datetime.now(timezone.utc)
    rental = NumberRental(
        id=f"rental_{int(now.timestamp() * 1000)}",
        user_id=user.id,
        phone_number=details.get("number"),
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
    
    # For now, return placeholder - would integrate with TextVerified rental API
    return {
        "rental_id": rental.id,
        "phone_number": rental.phone_number,
        "messages": [],
        "note": "Message retrieval for rentals coming soon"
    }

# CORS for frontend
from fastapi.middleware.cors import CORSMiddleware

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

# Rate Limiting with Redis
import redis
from time import time

# Initialize Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
except:
    redis_client = None
    REDIS_AVAILABLE = False
    print("Redis not available, using in-memory rate limiting")

def check_rate_limit(user_id: str, limit: int = 100, window: int = 60):
    """Check if user exceeded rate limit (100 req/min)"""
    if not REDIS_AVAILABLE:
        return True  # Skip rate limiting if Redis unavailable
    
    try:
        key = f"rate_limit:{user_id}"
        now = time()
        
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
