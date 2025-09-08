#!/usr/bin/env python3
"""
Database models for CumApp Communication Platform
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid

Base = declarative_base()

class MessageType(enum.Enum):
    INTERNAL = "internal"  # User to user within platform
    SMS_OUTBOUND = "sms_outbound"  # Platform user to external phone
    SMS_INBOUND = "sms_inbound"  # External phone to platform user
    SYSTEM = "system"  # System notifications

class MessageStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class SubscriptionTier(enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class NumberStatus(enum.Enum):
    AVAILABLE = "available"
    PURCHASED = "purchased"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    avatar_url = Column(String(255))
    
    # Subscription info
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_expires = Column(DateTime)
    
    # Usage limits
    monthly_sms_limit = Column(Integer, default=100)
    monthly_sms_used = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    owned_numbers = relationship("PhoneNumber", back_populates="owner")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient")
    conversations = relationship("ConversationParticipant", back_populates="user")

class PhoneNumber(Base):
    __tablename__ = "phone_numbers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = Column(String(20), unique=True, nullable=False)
    country_code = Column(String(3), nullable=False)
    area_code = Column(String(10))
    
    # Ownership
    owner_id = Column(String, ForeignKey("users.id"))
    
    # Pricing
    monthly_cost = Column(Float, default=1.00)
    sms_cost = Column(Float, default=0.0075)
    
    # Status
    status = Column(Enum(NumberStatus), default=NumberStatus.AVAILABLE)
    purchased_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Provider info
    provider = Column(String(50), default="mock")  # twilio, vonage, etc.
    provider_sid = Column(String(100))
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="owned_numbers")
    messages = relationship("Message", back_populates="phone_number")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100))  # Optional name for group chats
    is_group = Column(Boolean, default=False)
    
    # External number info (for SMS conversations)
    external_number = Column(String(20))  # If chatting with external number
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_message_at = Column(DateTime, default=func.now())
    
    # Relationships
    participants = relationship("ConversationParticipant", back_populates="conversation")
    messages = relationship("Message", back_populates="conversation")

class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    user_id = Column(String, ForeignKey("users.id"))
    
    # Participant settings
    is_admin = Column(Boolean, default=False)
    notifications_enabled = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=func.now())
    last_read_at = Column(DateTime, default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User", back_populates="conversations")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    sender_id = Column(String, ForeignKey("users.id"))
    recipient_id = Column(String, ForeignKey("users.id"))  # For direct messages
    
    # Message content
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.INTERNAL)
    
    # SMS specific fields
    phone_number_id = Column(String, ForeignKey("phone_numbers.id"))  # Which number was used
    external_number = Column(String(20))  # External phone number
    
    # Status tracking
    status = Column(Enum(MessageStatus), default=MessageStatus.PENDING)
    provider_message_id = Column(String(100))  # Twilio SID, etc.
    
    # Metadata
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_messages")
    phone_number = relationship("PhoneNumber", back_populates="messages")

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    
    # Contact info
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20))
    email = Column(String(100))
    notes = Column(Text)
    
    # Contact type
    is_platform_user = Column(Boolean, default=False)  # Is this contact also a platform user?
    platform_user_id = Column(String, ForeignKey("users.id"))
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Usage(Base):
    __tablename__ = "usage"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    
    # Usage tracking
    date = Column(DateTime, default=func.now())
    sms_sent = Column(Integer, default=0)
    sms_received = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    
    # Breakdown by provider/number
    phone_number_id = Column(String, ForeignKey("phone_numbers.id"))
    provider = Column(String(50))

# Database setup functions
def create_database_engine(database_url: str = "sqlite:///smsproj.db"):
    """Create database engine"""
    engine = create_engine(database_url, echo=True)
    return engine

def create_tables(engine):
    """Create all tables"""
    Base.metadata.create_all(engine)

def get_session_maker(engine):
    """Get session maker"""
    return sessionmaker(bind=engine)

# Example usage
if __name__ == "__main__":
    # Create database and tables
    engine = create_database_engine()
    create_tables(engine)
    print("✅ Database tables created successfully!")