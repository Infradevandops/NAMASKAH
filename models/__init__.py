#!/usr/bin/env python3
"""
Models package initialization
"""
from models.user_models import (
    Base, User, Session as UserSession, APIKey, VerificationRequest, PhoneNumber,
    UserRole, SubscriptionPlan, UserCreate, UserResponse
)
from models.conversation_models import (
    Conversation, Message, conversation_participants,
    ConversationStatus, MessageType,
    ConversationCreate, ConversationUpdate, ConversationResponse,
    MessageCreate, MessageUpdate, MessageResponse,
    ConversationListResponse, MessageListResponse,
    ConversationFilters, MessageFilters
)

# Set up the many-to-many relationship after both models are imported
from sqlalchemy.orm import relationship

# Add conversation relationships to User model
User.conversations = relationship(
    "Conversation", 
    secondary=conversation_participants, 
    back_populates="participants"
)

User.sent_messages = relationship(
    "Message", 
    foreign_keys="Message.sender_id", 
    back_populates="sender"
)

__all__ = [
    # Base
    "Base",
    
    # User models
    "User", "UserSession", "APIKey", "VerificationRequest", "PhoneNumber",
    "UserRole", "SubscriptionPlan",
    "UserCreate", "UserResponse",
    
    # Conversation models
    "Conversation", "Message", "conversation_participants",
    "ConversationStatus", "MessageType",
    "ConversationCreate", "ConversationUpdate", "ConversationResponse",
    "MessageCreate", "MessageUpdate", "MessageResponse",
    "ConversationListResponse", "MessageListResponse",
    "ConversationFilters", "MessageFilters"
]