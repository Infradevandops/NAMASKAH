#!/usr/bin/env python3
"""
Enhanced Conversation and Message Models for CumApp Platform
"""
import uuid
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, ForeignKey, 
    Enum, Table, Integer, Index
)
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from models.user_models import Base

# Enums
class ConversationStatus(enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    BLOCKED = "blocked"

class MessageType(enum.Enum):
    CHAT = "chat"                    # Internal chat messages
    SMS_OUTBOUND = "sms_outbound"    # SMS sent to external number
    SMS_INBOUND = "sms_inbound"      # SMS received from external number
    SYSTEM = "system"                # System notifications
    INTERNAL = "internal"            # Legacy support

# Association table for conversation participants
conversation_participants = Table(
    'conversation_participants',
    Base.metadata,
    Column('conversation_id', String, ForeignKey('conversations.id'), primary_key=True),
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('joined_at', DateTime, default=datetime.utcnow),
    Column('last_read_at', DateTime, default=datetime.utcnow),
    Column('is_admin', Boolean, default=False),
    Column('notifications_enabled', Boolean, default=True),
    extend_existing=True
)

# SQLAlchemy Models
class Conversation(Base):
    __tablename__ = "conversations"
    
    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Optional[str] = Column(String(255))
    is_group: bool = Column(Boolean, default=False)
    external_number: Optional[str] = Column(String(20))
    status: ConversationStatus = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)
    
    # Metadata
    created_by: str = Column(String, ForeignKey("users.id"), nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at: Optional[datetime] = Column(DateTime)
    
    # Settings
    is_archived: bool = Column(Boolean, default=False)
    is_muted: bool = Column(Boolean, default=False)
    
    # Relationships
    participants = relationship(
        "User", 
        secondary=conversation_participants, 
        back_populates="conversations"
    )
    messages = relationship(
        "Message", 
        back_populates="conversation", 
        order_by="Message.created_at",
        cascade="all, delete-orphan"
    )
    creator = relationship("User", foreign_keys=[created_by])
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_conversation_status', 'status'),
        Index('idx_conversation_created_by', 'created_by'),
        Index('idx_conversation_last_message', 'last_message_at'),
        Index('idx_conversation_external_number', 'external_number'),
        {'extend_existing': True}
    )

class Message(Base):
    __tablename__ = "messages"
    
    id: str = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: str = Column(String, ForeignKey("conversations.id"), nullable=False)
    sender_id: Optional[str] = Column(String, ForeignKey("users.id"))
    
    # Content
    content: str = Column(Text, nullable=False)
    message_type: MessageType = Column(Enum(MessageType), default=MessageType.CHAT)
    
    # External message details
    external_message_id: Optional[str] = Column(String(255))
    from_number: Optional[str] = Column(String(20))
    to_number: Optional[str] = Column(String(20))
    
    # Status tracking
    is_delivered: bool = Column(Boolean, default=False)
    is_read: bool = Column(Boolean, default=False)
    delivery_status: Optional[str] = Column(String(50))
    
    # Metadata
    is_edited: bool = Column(Boolean, default=False)
    is_deleted: bool = Column(Boolean, default=False)
    
    # Timestamps
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    delivered_at: Optional[datetime] = Column(DateTime)
    read_at: Optional[datetime] = Column(DateTime)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_message_conversation', 'conversation_id'),
        Index('idx_message_sender', 'sender_id'),
        Index('idx_message_created_at', 'created_at'),
        Index('idx_message_type', 'message_type'),
        Index('idx_message_delivery_status', 'is_delivered', 'is_read'),
        {'extend_existing': True}
    )

# Pydantic Models for API
class ConversationCreate(BaseModel):
    title: Optional[str] = None
    is_group: bool = False
    external_number: Optional[str] = None
    participant_ids: list[str] = Field(default_factory=list)

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None
    is_muted: Optional[bool] = None
    status: Optional[ConversationStatus] = None

class ConversationResponse(BaseModel):
    id: str
    title: Optional[str]
    is_group: bool
    external_number: Optional[str]
    status: ConversationStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]
    is_archived: bool
    is_muted: bool
    participant_count: int
    unread_count: int = 0
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    content: str
    message_type: MessageType = MessageType.CHAT
    to_number: Optional[str] = None

class MessageUpdate(BaseModel):
    content: Optional[str] = None
    is_read: Optional[bool] = None

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: Optional[str]
    content: str
    message_type: MessageType
    external_message_id: Optional[str]
    from_number: Optional[str]
    to_number: Optional[str]
    is_delivered: bool
    is_read: bool
    delivery_status: Optional[str]
    is_edited: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    sender_username: Optional[str] = None
    
    class Config:
        from_attributes = True

class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total_count: int
    unread_total: int

class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    total_count: int
    has_more: bool
    next_cursor: Optional[str] = None

# Search and filter models
class ConversationFilters(BaseModel):
    status: Optional[ConversationStatus] = None
    is_group: Optional[bool] = None
    is_archived: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

class MessageFilters(BaseModel):
    message_type: Optional[MessageType] = None
    sender_id: Optional[str] = None
    is_read: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search_query: Optional[str] = None