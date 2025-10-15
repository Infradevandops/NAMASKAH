"""Namaskah SMS - Minimal TextVerified SMS Verification API"""
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
    created_at = Column(DateTime, default=datetime.utcnow)

class Verification(Base):
    __tablename__ = "verifications"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    service_name = Column(String, nullable=False)
    phone_number = Column(String)
    status = Column(String, default="pending")
    verification_code = Column(String)
    cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

Base.metadata.create_all(bind=engine)

# Schemas
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class CreateVerificationRequest(BaseModel):
    service_name: str
    capability: str = "sms"

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
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
def health():
    return {"status": "healthy", "service": "namaskah-sms"}

@app.post("/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        id=f"user_{datetime.now(timezone.utc).timestamp()}",
        email=req.email,
        password_hash=bcrypt.hash(req.password)
    )
    db.add(user)
    db.commit()
    
    token = jwt.encode({"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(days=30)}, JWT_SECRET)
    return {"token": token, "user_id": user.id}

@app.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not bcrypt.verify(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = jwt.encode({"user_id": user.id, "exp": datetime.now(timezone.utc) + timedelta(days=30)}, JWT_SECRET)
    return {"token": token, "user_id": user.id}

@app.get("/auth/me")
def get_me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "created_at": user.created_at}

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
                "created_at": v.created_at
            }
            for v in verifications
        ]
    }

@app.post("/verify/create")
def create_verification(req: CreateVerificationRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    verification_id = tv_client.create_verification(req.service_name, req.capability)
    details = tv_client.get_verification(verification_id)
    
    verification = Verification(
        id=verification_id,
        user_id=user.id,
        service_name=req.service_name,
        phone_number=details.get("number"),
        status="pending"
    )
    db.add(verification)
    db.commit()
    
    return {
        "id": verification.id,
        "service_name": verification.service_name,
        "phone_number": verification.phone_number,
        "status": verification.status
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
        "created_at": verification.created_at
    }

@app.get("/verify/{verification_id}/messages")
def get_messages(verification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    verification = db.query(Verification).filter(
        Verification.id == verification_id,
        Verification.user_id == user.id
    ).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    messages = tv_client.get_messages(verification_id)
    return {"verification_id": verification_id, "messages": messages}

@app.delete("/verify/{verification_id}")
def cancel_verification(verification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    verification = db.query(Verification).filter(
        Verification.id == verification_id,
        Verification.user_id == user.id
    ).first()
    
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    tv_client.cancel_verification(verification_id)
    verification.status = "cancelled"
    db.commit()
    
    return {"message": "Verification cancelled"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
