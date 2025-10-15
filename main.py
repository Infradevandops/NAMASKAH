"""Namaskah SMS - With Pricing & Admin Panel"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.hash import bcrypt
import requests

load_dotenv()

# Config
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sms.db")
TEXTVERIFIED_API_KEY = os.getenv("TEXTVERIFIED_API_KEY")
TEXTVERIFIED_EMAIL = os.getenv("TEXTVERIFIED_EMAIL")
VERIFICATION_COST = 0.50  # ₵0.50 per verification
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
Base = declarative_base()

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    credits = Column(Float, default=5.0)  # Free credits
    is_admin = Column(Boolean, default=False)
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
    status = Column(String, default="pending")
    verification_code = Column(String)
    cost = Column(Float, default=VERIFICATION_COST)
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
app = FastAPI(title="Namaskah SMS", version="2.0.0")

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

@app.get("/reviews")
async def reviews_page(request: Request):
    return templates.TemplateResponse("reviews.html", {"request": request})

@app.get("/admin")
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/health")
def health():
    return {"status": "healthy", "service": "namaskah-sms"}

@app.get("/services/list")
def get_services_list():
    """Get categorized services"""
    try:
        import json
        with open('services_categorized.json', 'r') as f:
            data = json.load(f)
        return data
    except:
        return {"categories": {}, "uncategorized": [], "pricing": {"categorized": 0.50, "uncategorized": 0.75}}

@app.post("/auth/register")
def register(req: RegisterRequest, referral_code: str = None, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    import secrets
    user_referral_code = secrets.token_urlsafe(6)
    
    user = User(
        id=f"user_{datetime.now(timezone.utc).timestamp()}",
        email=req.email,
        password_hash=bcrypt.hash(req.password),
        credits=5.0,
        referral_code=user_referral_code
    )
    
    # Handle referral
    if referral_code:
        referrer = db.query(User).filter(User.referral_code == referral_code).first()
        if referrer:
            user.referred_by = referrer.id
            user.credits += 2.0  # Bonus for being referred
            referrer.credits += 1.0  # Reward referrer
            referrer.referral_earnings += 1.0
            
            # Create referral record
            referral = Referral(
                id=f"ref_{datetime.now(timezone.utc).timestamp()}",
                referrer_id=referrer.id,
                referred_id=user.id,
                reward_amount=1.0
            )
            db.add(referral)
            
            # Create transactions
            db.add(Transaction(
                id=f"txn_{datetime.now(timezone.utc).timestamp()}",
                user_id=referrer.id,
                amount=1.0,
                type="credit",
                description=f"Referral bonus from {user.email}"
            ))
            db.add(Transaction(
                id=f"txn_{datetime.now(timezone.utc).timestamp() + 0.001}",
                user_id=user.id,
                amount=2.0,
                type="credit",
                description="Referral signup bonus"
            ))
    
    db.add(user)
    db.commit()
    
    token = jwt.encode({"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(days=30)}, JWT_SECRET)
    return {"token": token, "user_id": user.id, "credits": user.credits, "referral_code": user.referral_code}

@app.post("/auth/google")
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
                credits=5.0,
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

@app.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
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

@app.get("/auth/me")
def get_me(user: User = Depends(get_current_user)):
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
        "is_admin": user.is_admin,
        "created_at": user.created_at
    }

@app.get("/verifications/history")
def get_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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

@app.get("/transactions/history")
def get_transactions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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

@app.post("/verify/create")
def create_verification(req: CreateVerificationRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Determine cost based on category
    import json
    try:
        with open('services_categorized.json', 'r') as f:
            data = json.load(f)
        
        is_categorized = False
        for category_services in data['categories'].values():
            if req.service_name in category_services:
                is_categorized = True
                break
        
        cost = data['pricing']['categorized'] if is_categorized else data['pricing']['uncategorized']
    except:
        cost = VERIFICATION_COST
    
    # Check credits
    if user.credits < cost:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need ₵{cost}, have ₵{user.credits}")
    
    # Deduct credits
    user.credits -= cost
    
    # Check low balance and send notification
    settings = db.query(NotificationSettings).filter(NotificationSettings.user_id == user.id).first()
    threshold = settings.low_balance_threshold if settings else 1.0
    
    if user.credits <= threshold and (not settings or settings.email_on_low_balance):
        send_email(
            user.email,
            "⚠️ Low Balance Alert - Namaskah SMS",
            f"""<h2>⚠️ Low Balance Alert</h2>
            <p>Your wallet balance is low: <strong>₵{user.credits:.2f}</strong></p>
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
        status="pending",
        cost=cost
    )
    db.add(verification)
    db.commit()
    
    return {
        "id": verification.id,
        "service_name": verification.service_name,
        "phone_number": verification.phone_number,
        "status": verification.status,
        "cost": verification.cost,
        "remaining_credits": user.credits
    }

@app.get("/verify/{verification_id}")
def get_verification(verification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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

@app.get("/verify/{verification_id}/messages")
async def get_messages(verification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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

@app.delete("/verify/{verification_id}")
def cancel_verification(verification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
@app.get("/admin/users")
def get_all_users(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
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

@app.post("/admin/credits/add")
def add_credits(req: AddCreditsRequest, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
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
    
    return {"message": f"Added ${req.amount} credits", "new_balance": user.credits}

@app.get("/admin/stats")
def get_stats(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_verifications = db.query(Verification).count()
    total_revenue = db.query(Transaction).filter(Transaction.type == "debit").count() * VERIFICATION_COST
    
    return {
        "total_users": total_users,
        "total_verifications": total_verifications,
        "total_revenue": total_revenue,
        "verification_cost": VERIFICATION_COST
    }

# Payment Endpoints
@app.post("/wallet/fund")
def fund_wallet(req: FundWalletRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.amount < 5:
        raise HTTPException(status_code=400, detail="Minimum funding amount is $5.00")
    
    payment_methods = {
        'paystack': '🏦 Paystack',
        'bitcoin': '₿ Bitcoin',
        'ethereum': 'Ξ Ethereum',
        'solana': '◎ Solana',
        'usdt': '₮ USDT'
    }
    
    if req.payment_method not in payment_methods:
        raise HTTPException(status_code=400, detail="Invalid payment method")
    
    # Add credits (1 USD = 1 Namaskah Coin)
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
    db.commit()
    
    return {
        "success": True,
        "amount": req.amount,
        "new_balance": user.credits,
        "payment_method": payment_methods[req.payment_method],
        "message": f"Successfully added ₵{req.amount:.2f} to your wallet"
    }

@app.post("/wallet/paystack/initialize")
def initialize_paystack(req: FundWalletRequest, user: User = Depends(get_current_user)):
    """Initialize Paystack payment"""
    if req.amount < 5:
        raise HTTPException(status_code=400, detail="Minimum funding amount is $5.00")
    
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
                "callback_url": "http://localhost:8000/app",
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

@app.post("/wallet/crypto/address")
def get_crypto_address(req: FundWalletRequest, user: User = Depends(get_current_user)):
    """Get crypto payment address"""
    if req.amount < 5:
        raise HTTPException(status_code=400, detail="Minimum funding amount is $5.00")
    
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
        "instructions": f"Send exactly ${req.amount} USD worth of {req.payment_method.upper()} to the address above"
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
@app.post("/api-keys/create")
def create_api_key(req: CreateAPIKeyRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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

@app.get("/api-keys/list")
def list_api_keys(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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

@app.delete("/api-keys/{key_id}")
def delete_api_key(key_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(key)
    db.commit()
    return {"message": "API key deleted"}

# Webhook Endpoints
@app.post("/webhooks/create")
def create_webhook(req: CreateWebhookRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    webhook = Webhook(
        id=f"webhook_{datetime.now(timezone.utc).timestamp()}",
        user_id=user.id,
        url=req.url
    )
    db.add(webhook)
    db.commit()
    
    return {"id": webhook.id, "url": webhook.url, "is_active": webhook.is_active}

@app.get("/webhooks/list")
def list_webhooks(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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

@app.delete("/webhooks/{webhook_id}")
def delete_webhook(webhook_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
@app.get("/analytics/dashboard")
def get_analytics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
@app.get("/notifications/settings")
def get_notification_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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

@app.post("/notifications/settings")
def update_notification_settings(email_on_sms: bool = True, email_on_low_balance: bool = True, 
                                low_balance_threshold: float = 1.0,
                                user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
@app.get("/referrals/stats")
def get_referral_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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

# CORS for frontend
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
from collections import defaultdict
from time import time

rate_limit_store = defaultdict(list)

def check_rate_limit(user_id: str, limit: int = 100, window: int = 60):
    """Check if user exceeded rate limit (100 req/min)"""
    now = time()
    requests = rate_limit_store[user_id]
    
    # Remove old requests outside window
    rate_limit_store[user_id] = [req_time for req_time in requests if now - req_time < window]
    
    if len(rate_limit_store[user_id]) >= limit:
        return False
    
    rate_limit_store[user_id].append(now)
    return True

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
