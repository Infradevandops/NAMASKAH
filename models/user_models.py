#!/usr/bin/env python3
"""
User Management Models for CumApp Communication Platform
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table, Index
from sqlalchemy.orm import relationship
import uuid

# Use declarative_base directly to avoid circular imports
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    PREMIUM = "premium"

class SubscriptionPlan(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class MessageType(str, Enum):
    SMS = "sms"
    VOICE = "voice"
    CHAT = "chat"
    VERIFICATION = "verification"

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    BLOCKED = "blocked"

# Association table for conversation participants
conversation_participants = Table(
    'conversation_participants',
    Base.metadata,
    Column('conversation_id', String, ForeignKey('conversations.id')),
    Column('user_id', String, ForeignKey('users.id'))
)

class User(Base):
    """User model for the communication platform"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String, default=UserRole.USER)
    
    # Subscription info
    subscription_plan = Column(String, default=SubscriptionPlan.FREE)
    subscription_expires = Column(DateTime)
    
    # Usage limits
    monthly_sms_limit = Column(Integer, default=100)
    monthly_sms_used = Column(Integer, default=0)
    monthly_voice_minutes_limit = Column(Integer, default=60)
    monthly_voice_minutes_used = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # API access (deprecated - use APIKey model instead)
    api_calls_today = Column(Integer, default=0)
    api_rate_limit = Column(Integer, default=1000)
    
    # Email verification
    email_verification_token = Column(String)
    email_verification_expires = Column(DateTime)
    
    # Password reset
    password_reset_token = Column(String)
    password_reset_expires = Column(DateTime)
    
    # Relationships
    owned_numbers = relationship("PhoneNumber", back_populates="owner")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    verification_requests = relationship("VerificationRequest", back_populates="user")
    
    # Note: Conversation relationships are defined in conversation_models.py to avoid circular imports

    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_username', 'username'),
        Index('idx_user_active', 'is_active'),
    )

class PhoneNumber(Base):
    """Phone numbers owned by users"""
    __tablename__ = "phone_numbers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = Column(String, unique=True, nullable=False)
    country_code = Column(String, nullable=False)
    provider = Column(String, nullable=False)  # twilio, vonage, etc.
    
    # Ownership
    owner_id = Column(String, ForeignKey("users.id"))
    owner = relationship("User", back_populates="owned_numbers")
    
    # Subscription details
    monthly_cost = Column(String)
    sms_cost_per_message = Column(String)
    voice_cost_per_minute = Column(String)
    
    # Status
    is_active = Column(Boolean, default=True)
    purchased_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Usage stats
    total_sms_sent = Column(Integer, default=0)
    total_sms_received = Column(Integer, default=0)
    total_voice_minutes = Column(Integer, default=0)
    
    # Enhanced fields for marketplace
    area_code = Column(String)
    region = Column(String)
    provider_id = Column(String)  # Provider's internal ID
    setup_fee = Column(String, default="0.00")
    auto_renew = Column(Boolean, default=True)
    status = Column(String, default="active")  # active, suspended, expired, cancelled
    capabilities = Column(String)  # JSON array of capabilities
    
    # Enhanced usage tracking
    monthly_sms_sent = Column(Integer, default=0)
    monthly_voice_minutes = Column(Integer, default=0)
    last_renewal_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_phone_number_status', 'status'),
        Index('idx_phone_number_country', 'country_code'),
        Index('idx_phone_number_owner', 'owner_id'),
        Index('idx_phone_number_provider', 'provider'),
        {'extend_existing': True}
    )

class Conversation(Base):
    """Conversations between users and external numbers"""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String)
    
    # Conversation type and participants
    is_group = Column(Boolean, default=False)
    external_number = Column(String)  # For conversations with external numbers
    
    # Status
    status = Column(String, default=ConversationStatus.ACTIVE)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = Column(DateTime)
    
    # Relationships
    participants = relationship("User", secondary=conversation_participants, back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")

class Message(Base):
    """Messages in conversations"""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    sender_id = Column(String, ForeignKey("users.id"))
    
    # Message content
    content = Column(Text, nullable=False)
    message_type = Column(String, default=MessageType.CHAT)
    
    # External message details (for SMS/Voice)
    external_message_id = Column(String)  # Twilio SID, etc.
    from_number = Column(String)
    to_number = Column(String)
    
    # Status
    is_delivered = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    delivery_status = Column(String)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")

class Session(Base):
    """User sessions for JWT refresh token management"""
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    refresh_token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    user_agent = Column(String)
    ip_address = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index('idx_session_refresh_token', 'refresh_token'),
        Index('idx_session_user_active', 'user_id', 'is_active'),
    )

class APIKey(Base):
    """API keys for programmatic access"""
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    scopes = Column(Text)  # JSON array of permissions
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Usage tracking
    total_requests = Column(Integer, default=0)
    requests_today = Column(Integer, default=0)
    last_request_date = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    __table_args__ = (
        Index('idx_apikey_hash', 'key_hash'),
        Index('idx_apikey_user_active', 'user_id', 'is_active'),
    )

class VerificationRequest(Base):
    """TextVerified verification requests"""
    __tablename__ = "verification_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # TextVerified details
    textverified_id = Column(String, unique=True)
    service_name = Column(String, nullable=False)
    phone_number = Column(String)
    
    # Status
    status = Column(String, default="pending")  # pending, completed, failed, cancelled
    verification_code = Column(String)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=30))
    
    # Relationships
    user = relationship("User", back_populates="verification_requests")
    
    __table_args__ = (
        Index('idx_verification_user', 'user_id'),
        Index('idx_verification_textverified_id', 'textverified_id'),
        Index('idx_verification_status', 'status'),
    )

# Pydantic models for API
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    subscription_plan: SubscriptionPlan
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    title: Optional[str] = None
    external_number: Optional[str] = None
    is_group: bool = False
    participant_ids: List[str] = []

class ConversationResponse(BaseModel):
    id: str
    title: Optional[str]
    is_group: bool
    external_number: Optional[str]
    status: ConversationStatus
    created_at: datetime
    last_message_at: Optional[datetime]
    participant_count: int
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    conversation_id: str
    content: str
    message_type: MessageType = MessageType.CHAT
    to_number: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    content: str
    message_type: MessageType
    is_delivered: bool
    is_read: bool
    created_at: datetime
    from_number: Optional[str]
    to_number: Optional[str]
    
    class Config:
        from_attributes = True

class VerificationCreate(BaseModel):
    service_name: str
    capability: str = "sms"

class VerificationResponse(BaseModel):
    id: str
    textverified_id: str
    service_name: str
    phone_number: Optional[str]
    status: str
    verification_code: Optional[str]
    created_at: datetime
    expires_at: datetime
    
    class Config:
        from_attributes = True