#!/usr/bin/env python3
"""
Phone Number Models for CumApp Platform
"""
import uuid
import enum
from datetime import datetime, timedelta
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, 
    Enum, Integer, Numeric, Index, Text
)
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from models.user_models import Base

# Enums
class PhoneNumberStatus(enum.Enum):
    AVAILABLE = "available"
    PURCHASED = "purchased"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class PhoneNumberProvider(enum.Enum):
    TWILIO = "twilio"
    TEXTVERIFIED = "textverified"
    MOCK = "mock"  # For development/testing

class PhoneNumberCapability(enum.Enum):
    SMS = "sms"
    VOICE = "voice"
    MMS = "mms"
    FAX = "fax"

# SQLAlchemy Models
class PhoneNumber(Base):
    """Phone numbers available for purchase or owned by users"""
    __tablename__ = "phone_numbers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Provider information
    provider = Column(Enum(PhoneNumberProvider), nullable=False)
    provider_id = Column(String)  # Provider's internal ID
    country_code = Column(String(3), nullable=False)
    area_code = Column(String(10))
    region = Column(String(100))
    
    # Ownership and status
    owner_id = Column(String, ForeignKey("users.id"))
    status = Column(Enum(PhoneNumberStatus), default=PhoneNumberStatus.AVAILABLE)
    
    # Pricing
    monthly_cost = Column(Numeric(10, 2))  # Monthly subscription cost
    sms_cost_per_message = Column(Numeric(10, 4))  # Cost per SMS
    voice_cost_per_minute = Column(Numeric(10, 4))  # Cost per voice minute
    setup_fee = Column(Numeric(10, 2), default=0)
    
    # Capabilities
    capabilities = Column(Text)  # JSON array of capabilities
    
    # Usage tracking
    total_sms_sent = Column(Integer, default=0)
    total_sms_received = Column(Integer, default=0)
    total_voice_minutes = Column(Integer, default=0)
    monthly_sms_sent = Column(Integer, default=0)
    monthly_voice_minutes = Column(Integer, default=0)
    
    # Subscription details
    purchased_at = Column(DateTime)
    expires_at = Column(DateTime)
    auto_renew = Column(Boolean, default=True)
    last_renewal_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="phone_numbers")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_phone_number_status', 'status'),
        Index('idx_phone_number_country', 'country_code'),
        Index('idx_phone_number_owner', 'owner_id'),
        Index('idx_phone_number_provider', 'provider'),
        Index('idx_phone_number_expires', 'expires_at'),
        {'extend_existing': True}
    )

class PhoneNumberUsage(Base):
    """Daily usage tracking for phone numbers"""
    __tablename__ = "phone_number_usage"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number_id = Column(String, ForeignKey("phone_numbers.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Usage date
    usage_date = Column(DateTime, nullable=False, index=True)
    
    # Usage metrics
    sms_sent = Column(Integer, default=0)
    sms_received = Column(Integer, default=0)
    voice_minutes = Column(Integer, default=0)
    
    # Costs
    sms_cost = Column(Numeric(10, 4), default=0)
    voice_cost = Column(Numeric(10, 4), default=0)
    total_cost = Column(Numeric(10, 4), default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    phone_number = relationship("PhoneNumber")
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_usage_phone_date', 'phone_number_id', 'usage_date'),
        Index('idx_usage_user_date', 'user_id', 'usage_date'),
        {'extend_existing': True}
    )

# Pydantic Models for API
class PhoneNumberSearch(BaseModel):
    country_code: str = Field(..., min_length=2, max_length=3)
    area_code: Optional[str] = None
    capabilities: List[PhoneNumberCapability] = Field(default_factory=lambda: [PhoneNumberCapability.SMS])
    limit: int = Field(default=20, ge=1, le=100)

class AvailablePhoneNumber(BaseModel):
    phone_number: str
    country_code: str
    area_code: Optional[str]
    region: Optional[str]
    provider: PhoneNumberProvider
    monthly_cost: Decimal
    sms_cost_per_message: Decimal
    voice_cost_per_minute: Optional[Decimal]
    setup_fee: Decimal
    capabilities: List[PhoneNumberCapability]
    
    class Config:
        from_attributes = True

class PhoneNumberPurchase(BaseModel):
    phone_number: str
    auto_renew: bool = True

class OwnedPhoneNumber(BaseModel):
    id: str
    phone_number: str
    country_code: str
    area_code: Optional[str]
    region: Optional[str]
    provider: PhoneNumberProvider
    status: PhoneNumberStatus
    monthly_cost: Decimal
    purchased_at: datetime
    expires_at: datetime
    auto_renew: bool
    
    # Usage statistics
    total_sms_sent: int
    total_sms_received: int
    total_voice_minutes: int
    monthly_sms_sent: int
    monthly_voice_minutes: int
    
    class Config:
        from_attributes = True

class PhoneNumberUsageStats(BaseModel):
    phone_number_id: str
    phone_number: str
    period_start: datetime
    period_end: datetime
    
    # Usage metrics
    total_sms_sent: int
    total_sms_received: int
    total_voice_minutes: int
    
    # Cost breakdown
    sms_cost: Decimal
    voice_cost: Decimal
    monthly_fee: Decimal
    total_cost: Decimal
    
    # Daily breakdown
    daily_usage: List[dict] = Field(default_factory=list)

class PhoneNumberRenewal(BaseModel):
    phone_number_id: str
    renewal_period_months: int = Field(default=1, ge=1, le=12)
    auto_renew: Optional[bool] = None

class PhoneNumberResponse(BaseModel):
    success: bool
    message: str
    phone_number: Optional[OwnedPhoneNumber] = None
    transaction_id: Optional[str] = None

class PhoneNumberListResponse(BaseModel):
    phone_numbers: List[AvailablePhoneNumber]
    total_count: int
    country_code: str
    area_code: Optional[str]

class OwnedPhoneNumberListResponse(BaseModel):
    phone_numbers: List[OwnedPhoneNumber]
    total_count: int
    active_count: int
    total_monthly_cost: Decimal