#!/usr/bin/env python3
"""
Unit tests for Conversation Service
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import (
    Base, User, Conversation, Message, 
    ConversationStatus, MessageType, UserRole, SubscriptionPlan,
    ConversationCreate, ConversationUpdate, MessageCreate, MessageUpdate,
    ConversationFilters, MessageFilters
)
from services.conversation_service import ConversationService
from auth.security import hash_password

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_conversation_service.db"
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
    for i in range(5):
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

@pytest.fixture
def conversation_service(db_session):
    """Create conversation service instance"""
    return ConversationService(db_session)

class TestConversationCRUD:
    """Test conversation CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_conversation_basic(self, conversation_service, test_users):
        """Test creating a basic conversation"""
        creator = test_users[0]
        participant = test_users[1]
        
        conversation_data = ConversationCreate(
            title="Test Conversation",
            is_group=False,
            participant_ids=[participant.id]
        )
        
        conversation = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        assert conversation.id is not None
        assert conversation.title == "Test Conversation"
        assert conversation.created_by == creator.id
        assert conversation.is_group is False
        assert conversation.status == ConversationStatus.ACTIVE
        assert len(conversation.participants) == 2  # Creator + participant
        assert creator in conversation.participants
        assert participant in conversation.participants
    
    @pytest.mark.asyncio
    async def test_create_group_conversation(self, conversation_service, test_users):
        """Test creating a group conversation"""
        creator = test_users[0]
        participants = test_users[1:4]
        
        conversation_data = ConversationCreate(
            title="Group Chat",
            is_group=True,
            participant_ids=[p.id for p in participants]
        )
        
        conversation = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        assert conversation.is_group is True
        assert len(conversation.participants) == 4  # Creator + 3 participants
        assert conversation.title == "Group Chat"
    
    @pytest.mark.asyncio
    async def test_create_sms_conversation(self, conversation_service, test_users):
        """Test creating SMS conversation with external number"""
        creator = test_users[0]
        
        conversation_data = ConversationCreate(
            title="SMS Chat",
            is_group=False,
            external_number="+1234567890"
        )
        
        conversation = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        assert conversation.external_number == "+1234567890"
        assert len(conversation.participants) == 1  # Only creator
    
    @pytest.mark.asyncio
    async def test_get_conversation_success(self, conversation_service, test_users):
        """Test getting conversation by participant"""
        creator = test_users[0]
        participant = test_users[1]
        
        # Create conversation
        conversation_data = ConversationCreate(
            title="Test Get",
            participant_ids=[participant.id]
        )
        
        created_conv = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        # Get conversation as participant
        retrieved_conv = await conversation_service.get_conversation(
            created_conv.id, participant.id
        )
        
        assert retrieved_conv is not None
        assert retrieved_conv.id == created_conv.id
        assert retrieved_conv.title == "Test Get"
    
    @pytest.mark.asyncio
    async def test_get_conversation_unauthorized(self, conversation_service, test_users):
        """Test getting conversation by non-participant"""
        creator = test_users[0]
        participant = test_users[1]
        outsider = test_users[2]
        
        # Create conversation
        conversation_data = ConversationCreate(
            title="Private Chat",
            participant_ids=[participant.id]
        )
        
        created_conv = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        # Try to get conversation as outsider
        retrieved_conv = await conversation_service.get_conversation(
            created_conv.id, outsider.id
        )
        
        assert retrieved_conv is None
    
    @pytest.mark.asyncio
    async def test_update_conversation(self, conversation_service, test_users):
        """Test updating conversation settings"""
        creator = test_users[0]
        
        # Create conversation
        conversation_data = ConversationCreate(title="Original Title")
        conversation = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        # Update conversation
        update_data = ConversationUpdate(
            title="Updated Title",
            is_archived=True,
            is_muted=True
        )
        
        updated_conv = await conversation_service.update_conversation(
            conversation.id, creator.id, update_data
        )
        
        assert updated_conv.title == "Updated Title"
        assert updated_conv.is_archived is True
        assert updated_conv.is_muted is True
    
    @pytest.mark.asyncio
    async def test_delete_conversation(self, conversation_service, test_users):
        """Test soft deleting conversation"""
        creator = test_users[0]
        
        # Create conversation
        conversation_data = ConversationCreate(title="To Delete")
        conversation = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        # Delete conversation
        result = await conversation_service.delete_conversation(
            conversation.id, creator.id
        )
        
        assert result is True
        
        # Verify conversation is marked as deleted
        deleted_conv = await conversation_service.get_conversation(
            conversation.id, creator.id
        )
        assert deleted_conv.status == ConversationStatus.DELETED

class TestParticipantManagement:
    """Test participant management operations"""
    
    @pytest.mark.asyncio
    async def test_add_participants(self, conversation_service, test_users):
        """Test adding participants to conversation"""
        creator = test_users[0]
        initial_participant = test_users[1]
        new_participants = test_users[2:4]
        
        # Create conversation
        conversation_data = ConversationCreate(
            title="Add Participants Test",
            participant_ids=[initial_participant.id]
        )
        
        conversation = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        # Add new participants
        result = await conversation_service.add_participants(
            conversation.id, creator.id, [p.id for p in new_participants]
        )
        
        assert result is True
        
        # Verify participants were added
        updated_conv = await conversation_service.get_conversation(
            conversation.id, creator.id
        )
        assert len(updated_conv.participants) == 4  # Creator + initial + 2 new
    
    @pytest.mark.asyncio
    async def test_remove_participant(self, conversation_service, test_users):
        """Test removing participant from conversation"""
        creator = test_users[0]
        participants = test_users[1:3]
        
        # Create conversation
        conversation_data = ConversationCreate(
            title="Remove Participant Test",
            participant_ids=[p.id for p in participants]
        )
        
        conversation = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        # Remove one participant
        result = await conversation_service.remove_participant(
            conversation.id, creator.id, participants[0].id
        )
        
        assert result is True
        
        # Verify participant was removed
        updated_conv = await conversation_service.get_conversation(
            conversation.id, creator.id
        )
        assert len(updated_conv.participants) == 2  # Creator + 1 remaining participant

class TestMessageOperations:
    """Test message operations"""
    
    @pytest.mark.asyncio
    async def test_send_chat_message(self, conversation_service, test_users):
        """Test sending a chat message"""
        creator = test_users[0]
        participant = test_users[1]
        
        # Create conversation
        conversation_data = ConversationCreate(
            title="Message Test",
            participant_ids=[participant.id]
        )
        
        conversation = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        # Send message
        message_data = MessageCreate(
            content="Hello, world!",
            message_type=MessageType.CHAT
        )
        
        message = await conversation_service.send_message(
            conversation.id, creator.id, message_data
        )
        
        assert message.id is not None
        assert message.content == "Hello, world!"
        assert message.sender_id == creator.id
        assert message.conversation_id == conversation.id
        assert message.message_type == MessageType.CHAT
    
    @pytest.mark.asyncio
    async def test_send_sms_message(self, conversation_service, test_users):
        """Test sending an SMS message"""
        creator = test_users[0]
        
        # Create SMS conversation
        conversation_data = ConversationCreate(
            title="SMS Test",
            external_number="+1234567890"
        )
        
        conversation = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        # Send SMS message
        message_data = MessageCreate(
            content="SMS message content",
            message_type=MessageType.SMS_OUTBOUND,
            to_number="+1234567890"
        )
        
        message = await conversation_service.send_message(
            conversation.id, creator.id, message_data
        )
        
        assert message.message_type == MessageType.SMS_OUTBOUND
        assert message.to_number == "+1234567890"
    
    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, conversation_service, test_users):
        """Test getting messages from conversation"""
        creator = test_users[0]
        participant = test_users[1]
        
        # Create conversation
        conversation_data = ConversationCreate(
            title="Messages Test",
            participant_ids=[participant.id]
        )
        
        conversation = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        # Send multiple messages
        for i in range(5):
            message_data = MessageCreate(content=f"Message {i}")
            await conversation_service.send_message(
                conversation.id, creator.id, message_data
            )
        
        # Get messages
        messages, total_count = await conversation_service.get_conversation_messages(
            conversation.id, creator.id, limit=3
        )
        
        assert len(messages) == 3
        assert total_count == 5
        assert messages[0].content == "Message 0"  # Chronological order
    
    @pytest.mark.asyncio
    async def test_update_message(self, conversation_service, test_users):
        """Test updating a message"""
        creator = test_users[0]
        
        # Create conversation and message
        conversation_data = ConversationCreate(title="Update Test")
        conversation = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        message_data = MessageCreate(content="Original content")
        message = await conversation_service.send_message(
            conversation.id, creator.id, message_data
        )
        
        # Update message
        update_data = MessageUpdate(content="Updated content")
        updated_message = await conversation_service.update_message(
            message.id, creator.id, update_data
        )
        
        assert updated_message.content == "Updated content"
        assert updated_message.is_edited is True
    
    @pytest.mark.asyncio
    async def test_delete_message(self, conversation_service, test_users):
        """Test soft deleting a message"""
        creator = test_users[0]
        
        # Create conversation and message
        conversation_data = ConversationCreate(title="Delete Test")
        conversation = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        message_data = MessageCreate(content="To be deleted")
        message = await conversation_service.send_message(
            conversation.id, creator.id, message_data
        )
        
        # Delete message
        result = await conversation_service.delete_message(
            message.id, creator.id
        )
        
        assert result is True

class TestSearchAndFiltering:
    """Test search and filtering functionality"""
    
    @pytest.mark.asyncio
    async def test_get_user_conversations(self, conversation_service, test_users):
        """Test getting user's conversations"""
        creator = test_users[0]
        participant = test_users[1]
        
        # Create multiple conversations
        for i in range(3):
            conversation_data = ConversationCreate(
                title=f"Conversation {i}",
                participant_ids=[participant.id]
            )
            await conversation_service.create_conversation(
                creator.id, conversation_data
            )
        
        # Get conversations for participant
        conversations, total_count = await conversation_service.get_user_conversations(
            participant.id, limit=2
        )
        
        assert len(conversations) == 2
        assert total_count == 3
    
    @pytest.mark.asyncio
    async def test_get_user_conversations_with_filters(self, conversation_service, test_users):
        """Test getting conversations with filters"""
        creator = test_users[0]
        
        # Create conversations with different statuses
        conv1_data = ConversationCreate(title="Active Conv")
        conv1 = await conversation_service.create_conversation(creator.id, conv1_data)
        
        conv2_data = ConversationCreate(title="Group Conv", is_group=True)
        conv2 = await conversation_service.create_conversation(creator.id, conv2_data)
        
        # Archive one conversation
        await conversation_service.update_conversation(
            conv1.id, creator.id, ConversationUpdate(is_archived=True)
        )
        
        # Filter for non-archived conversations
        filters = ConversationFilters(is_archived=False)
        conversations, total_count = await conversation_service.get_user_conversations(
            creator.id, filters=filters
        )
        
        assert total_count == 1
        assert conversations[0].title == "Group Conv"
    
    @pytest.mark.asyncio
    async def test_search_messages(self, conversation_service, test_users):
        """Test searching messages"""
        creator = test_users[0]
        
        # Create conversation
        conversation_data = ConversationCreate(title="Search Test")
        conversation = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        # Send messages with different content
        messages_content = [
            "Hello world",
            "Python is great",
            "Hello Python",
            "Goodbye world"
        ]
        
        for content in messages_content:
            message_data = MessageCreate(content=content)
            await conversation_service.send_message(
                conversation.id, creator.id, message_data
            )
        
        # Search for "Hello"
        messages, total_count = await conversation_service.search_messages(
            creator.id, "Hello"
        )
        
        assert total_count == 2
        assert all("Hello" in msg.content for msg in messages)
    
    @pytest.mark.asyncio
    async def test_mark_messages_as_read(self, conversation_service, test_users):
        """Test marking messages as read"""
        creator = test_users[0]
        participant = test_users[1]
        
        # Create conversation
        conversation_data = ConversationCreate(
            title="Read Test",
            participant_ids=[participant.id]
        )
        
        conversation = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        # Send messages from creator
        for i in range(3):
            message_data = MessageCreate(content=f"Message {i}")
            await conversation_service.send_message(
                conversation.id, creator.id, message_data
            )
        
        # Mark messages as read by participant
        marked_count = await conversation_service.mark_messages_as_read(
            conversation.id, participant.id
        )
        
        assert marked_count == 3
    
    @pytest.mark.asyncio
    async def test_get_unread_count(self, conversation_service, test_users):
        """Test getting unread message count"""
        creator = test_users[0]
        participant = test_users[1]
        
        # Create conversation
        conversation_data = ConversationCreate(
            title="Unread Test",
            participant_ids=[participant.id]
        )
        
        conversation = await conversation_service.create_conversation(
            creator.id, conversation_data
        )
        
        # Send messages from creator
        for i in range(5):
            message_data = MessageCreate(content=f"Unread message {i}")
            await conversation_service.send_message(
                conversation.id, creator.id, message_data
            )
        
        # Get unread count for participant
        unread_count = await conversation_service.get_unread_count(participant.id)
        
        assert unread_count == 5

class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_create_conversation_invalid_creator(self, conversation_service):
        """Test creating conversation with invalid creator"""
        conversation_data = ConversationCreate(title="Invalid Creator")
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await conversation_service.create_conversation(
                "invalid_user_id", conversation_data
            )
    
    @pytest.mark.asyncio
    async def test_create_conversation_invalid_participants(self, conversation_service, test_users):
        """Test creating conversation with invalid participants"""
        creator = test_users[0]
        
        conversation_data = ConversationCreate(
            title="Invalid Participants",
            participant_ids=["invalid_id_1", "invalid_id_2"]
        )
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await conversation_service.create_conversation(
                creator.id, conversation_data
            )
    
    @pytest.mark.asyncio
    async def test_send_message_invalid_conversation(self, conversation_service, test_users):
        """Test sending message to invalid conversation"""
        creator = test_users[0]
        
        message_data = MessageCreate(content="Invalid conversation")
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await conversation_service.send_message(
                "invalid_conversation_id", creator.id, message_data
            )

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])