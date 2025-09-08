#!/usr/bin/env python3
"""
Unit tests for Conversation and Message Models
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import (
    Base, User, Conversation, Message, conversation_participants,
    ConversationStatus, MessageType, UserRole, SubscriptionPlan
)
from auth.security import hash_password

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_conversation_models.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """Create a test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_users(db_session):
    """Create test users"""
    users = []
    for i in range(3):
        user = User(
            email=f"user{i}@example.com",
            username=f"user{i}",
            hashed_password=hash_password("TestPassword123!"),
            full_name=f"Test User {i}",
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        users.append(user)
    
    db_session.commit()
    for user in users:
        db_session.refresh(user)
    
    return users

class TestConversationModel:
    """Test cases for Conversation model"""
    
    def test_create_conversation_basic(self, db_session, test_users):
        """Test creating a basic conversation"""
        creator = test_users[0]
        
        conversation = Conversation(
            title="Test Conversation",
            created_by=creator.id,
            is_group=False
        )
        
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        assert conversation.id is not None
        assert conversation.title == "Test Conversation"
        assert conversation.created_by == creator.id
        assert conversation.is_group is False
        assert conversation.status == ConversationStatus.ACTIVE
        assert conversation.is_archived is False
        assert conversation.is_muted is False
        assert conversation.created_at is not None
        assert conversation.updated_at is not None
    
    def test_create_group_conversation(self, db_session, test_users):
        """Test creating a group conversation"""
        creator = test_users[0]
        
        conversation = Conversation(
            title="Group Chat",
            created_by=creator.id,
            is_group=True
        )
        
        # Add participants
        conversation.participants.extend(test_users)
        
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        assert conversation.is_group is True
        assert len(conversation.participants) == 3
        assert creator in conversation.participants
    
    def test_conversation_with_external_number(self, db_session, test_users):
        """Test conversation with external phone number"""
        creator = test_users[0]
        
        conversation = Conversation(
            title="SMS Conversation",
            created_by=creator.id,
            external_number="+1234567890",
            is_group=False
        )
        
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        assert conversation.external_number == "+1234567890"
    
    def test_conversation_status_enum(self, db_session, test_users):
        """Test conversation status enum values"""
        creator = test_users[0]
        
        for status in ConversationStatus:
            conversation = Conversation(
                title=f"Test {status.value}",
                created_by=creator.id,
                status=status
            )
            
            db_session.add(conversation)
            db_session.commit()
            db_session.refresh(conversation)
            
            assert conversation.status == status
    
    def test_conversation_archive_and_mute(self, db_session, test_users):
        """Test conversation archive and mute functionality"""
        creator = test_users[0]
        
        conversation = Conversation(
            title="Test Settings",
            created_by=creator.id
        )
        
        db_session.add(conversation)
        db_session.commit()
        
        # Test archiving
        conversation.is_archived = True
        db_session.commit()
        db_session.refresh(conversation)
        assert conversation.is_archived is True
        
        # Test muting
        conversation.is_muted = True
        db_session.commit()
        db_session.refresh(conversation)
        assert conversation.is_muted is True
    
    def test_conversation_relationships(self, db_session, test_users):
        """Test conversation relationships"""
        creator = test_users[0]
        
        conversation = Conversation(
            title="Relationship Test",
            created_by=creator.id
        )
        
        conversation.participants.append(test_users[1])
        
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        # Test creator relationship
        assert conversation.creator == creator
        
        # Test participants relationship
        assert len(conversation.participants) == 1
        assert test_users[1] in conversation.participants

class TestMessageModel:
    """Test cases for Message model"""
    
    def test_create_chat_message(self, db_session, test_users):
        """Test creating a basic chat message"""
        creator = test_users[0]
        sender = test_users[1]
        
        conversation = Conversation(
            title="Test Chat",
            created_by=creator.id
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        message = Message(
            conversation_id=conversation.id,
            sender_id=sender.id,
            content="Hello, world!",
            message_type=MessageType.CHAT
        )
        
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        assert message.id is not None
        assert message.conversation_id == conversation.id
        assert message.sender_id == sender.id
        assert message.content == "Hello, world!"
        assert message.message_type == MessageType.CHAT
        assert message.is_delivered is False
        assert message.is_read is False
        assert message.is_edited is False
        assert message.is_deleted is False
        assert message.created_at is not None
    
    def test_create_sms_message(self, db_session, test_users):
        """Test creating an SMS message"""
        creator = test_users[0]
        
        conversation = Conversation(
            title="SMS Test",
            created_by=creator.id,
            external_number="+1234567890"
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        message = Message(
            conversation_id=conversation.id,
            sender_id=creator.id,
            content="SMS message content",
            message_type=MessageType.SMS_OUTBOUND,
            from_number="+0987654321",
            to_number="+1234567890",
            external_message_id="twilio_msg_123"
        )
        
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        assert message.message_type == MessageType.SMS_OUTBOUND
        assert message.from_number == "+0987654321"
        assert message.to_number == "+1234567890"
        assert message.external_message_id == "twilio_msg_123"
    
    def test_message_delivery_tracking(self, db_session, test_users):
        """Test message delivery and read tracking"""
        creator = test_users[0]
        
        conversation = Conversation(
            title="Delivery Test",
            created_by=creator.id
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        message = Message(
            conversation_id=conversation.id,
            sender_id=creator.id,
            content="Delivery test message"
        )
        
        db_session.add(message)
        db_session.commit()
        
        # Test delivery
        message.is_delivered = True
        message.delivered_at = datetime.utcnow()
        message.delivery_status = "delivered"
        db_session.commit()
        db_session.refresh(message)
        
        assert message.is_delivered is True
        assert message.delivered_at is not None
        assert message.delivery_status == "delivered"
        
        # Test read receipt
        message.is_read = True
        message.read_at = datetime.utcnow()
        db_session.commit()
        db_session.refresh(message)
        
        assert message.is_read is True
        assert message.read_at is not None
    
    def test_message_editing_and_deletion(self, db_session, test_users):
        """Test message editing and soft deletion"""
        creator = test_users[0]
        
        conversation = Conversation(
            title="Edit Test",
            created_by=creator.id
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        message = Message(
            conversation_id=conversation.id,
            sender_id=creator.id,
            content="Original message"
        )
        
        db_session.add(message)
        db_session.commit()
        
        # Test editing
        message.content = "Edited message"
        message.is_edited = True
        db_session.commit()
        db_session.refresh(message)
        
        assert message.content == "Edited message"
        assert message.is_edited is True
        
        # Test soft deletion
        message.is_deleted = True
        db_session.commit()
        db_session.refresh(message)
        
        assert message.is_deleted is True
    
    def test_message_type_enum(self, db_session, test_users):
        """Test all message type enum values"""
        creator = test_users[0]
        
        conversation = Conversation(
            title="Type Test",
            created_by=creator.id
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        for msg_type in MessageType:
            message = Message(
                conversation_id=conversation.id,
                sender_id=creator.id,
                content=f"Test {msg_type.value} message",
                message_type=msg_type
            )
            
            db_session.add(message)
            db_session.commit()
            db_session.refresh(message)
            
            assert message.message_type == msg_type
    
    def test_message_relationships(self, db_session, test_users):
        """Test message relationships"""
        creator = test_users[0]
        sender = test_users[1]
        
        conversation = Conversation(
            title="Relationship Test",
            created_by=creator.id
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        message = Message(
            conversation_id=conversation.id,
            sender_id=sender.id,
            content="Relationship test message"
        )
        
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        
        # Test conversation relationship
        assert message.conversation == conversation
        
        # Test sender relationship
        assert message.sender == sender
        
        # Test reverse relationship
        assert message in conversation.messages

class TestConversationParticipants:
    """Test cases for conversation participants association"""
    
    def test_add_participants(self, db_session, test_users):
        """Test adding participants to conversation"""
        creator = test_users[0]
        
        conversation = Conversation(
            title="Participants Test",
            created_by=creator.id,
            is_group=True
        )
        
        # Add all users as participants
        conversation.participants.extend(test_users)
        
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        assert len(conversation.participants) == 3
        for user in test_users:
            assert user in conversation.participants
    
    def test_remove_participants(self, db_session, test_users):
        """Test removing participants from conversation"""
        creator = test_users[0]
        
        conversation = Conversation(
            title="Remove Test",
            created_by=creator.id,
            is_group=True
        )
        
        conversation.participants.extend(test_users)
        db_session.add(conversation)
        db_session.commit()
        
        # Remove one participant
        conversation.participants.remove(test_users[2])
        db_session.commit()
        db_session.refresh(conversation)
        
        assert len(conversation.participants) == 2
        assert test_users[2] not in conversation.participants
    
    def test_user_conversations_relationship(self, db_session, test_users):
        """Test user's conversations relationship"""
        creator = test_users[0]
        participant = test_users[1]
        
        # Create multiple conversations
        conversations = []
        for i in range(3):
            conv = Conversation(
                title=f"Test Conversation {i}",
                created_by=creator.id
            )
            conv.participants.append(participant)
            conversations.append(conv)
            db_session.add(conv)
        
        db_session.commit()
        
        # Refresh participant to get updated relationships
        db_session.refresh(participant)
        
        # Check that participant is in all conversations
        assert len(participant.conversations) == 3
        for conv in conversations:
            assert conv in participant.conversations

class TestModelValidation:
    """Test model validation and constraints"""
    
    def test_conversation_required_fields(self, db_session, test_users):
        """Test conversation required fields validation"""
        creator = test_users[0]
        
        # Test missing created_by (should fail)
        with pytest.raises(Exception):
            conversation = Conversation(title="Invalid")
            db_session.add(conversation)
            db_session.commit()
    
    def test_message_required_fields(self, db_session, test_users):
        """Test message required fields validation"""
        creator = test_users[0]
        
        conversation = Conversation(
            title="Test",
            created_by=creator.id
        )
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)
        
        # Test missing content (should fail)
        with pytest.raises(Exception):
            message = Message(
                conversation_id=conversation.id,
                sender_id=creator.id
                # Missing content
            )
            db_session.add(message)
            db_session.commit()
        
        # Test missing conversation_id (should fail)
        with pytest.raises(Exception):
            message = Message(
                sender_id=creator.id,
                content="Test message"
                # Missing conversation_id
            )
            db_session.add(message)
            db_session.commit()

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])