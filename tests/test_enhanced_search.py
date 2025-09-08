#!/usr/bin/env python3
"""
Tests for Enhanced Chat Search and Infinite Scroll Functionality
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from services.conversation_service import ConversationService
from models import User, Conversation, Message, MessageType, ConversationStatus

class TestEnhancedSearch:
    """Test enhanced message search functionality"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        return User(
            id="test-user-id",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            is_active=True
        )
    
    @pytest.fixture
    def mock_conversation(self):
        return Conversation(
            id="test-conversation-id",
            title="Test Conversation",
            is_group=False,
            created_by="test-user-id",
            status=ConversationStatus.ACTIVE
        )
    
    @pytest.fixture
    def mock_messages(self):
        base_time = datetime.utcnow()
        return [
            Message(
                id=f"msg-{i}",
                conversation_id="test-conversation-id",
                sender_id="test-user-id",
                content=f"Test message {i} with search terms",
                message_type=MessageType.CHAT,
                created_at=base_time - timedelta(minutes=i)
            )
            for i in range(10)
        ]
    
    def test_enhanced_message_search_basic(self, mock_db, mock_user, mock_messages):
        """Test basic message search functionality"""
        service = ConversationService(mock_db)
        
        # Mock database queries
        mock_db.query.return_value.join.return_value.filter.return_value.subquery.return_value = Mock()
        mock_db.query.return_value.options.return_value.filter.return_value.filter.return_value.count.return_value = len(mock_messages)
        mock_db.query.return_value.options.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_messages
        
        # Test search
        result_messages, total_count = await service.search_messages(
            user_id=mock_user.id,
            query="search terms",
            limit=10,
            offset=0
        )
        
        assert len(result_messages) == len(mock_messages)
        assert total_count == len(mock_messages)
    
    def test_enhanced_message_search_with_filters(self, mock_db, mock_user, mock_messages):
        """Test message search with filters"""
        service = ConversationService(mock_db)
        
        # Mock database queries
        mock_db.query.return_value.join.return_value.filter.return_value.subquery.return_value = Mock()
        mock_db.query.return_value.options.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 5
        mock_db.query.return_value.options.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_messages[:5]
        
        from models import MessageFilters
        filters = MessageFilters(
            message_type=MessageType.CHAT,
            sender_id="test-user-id",
            created_after=datetime.utcnow() - timedelta(days=1)
        )
        
        result_messages, total_count = await service.search_messages(
            user_id=mock_user.id,
            query="search terms",
            filters=filters,
            limit=10,
            offset=0
        )
        
        assert len(result_messages) == 5
        assert total_count == 5
    
    def test_conversation_search(self, mock_db, mock_user):
        """Test conversation search functionality"""
        service = ConversationService(mock_db)
        
        mock_conversations = [
            Conversation(
                id=f"conv-{i}",
                title=f"Test Conversation {i}",
                is_group=False,
                created_by=mock_user.id,
                status=ConversationStatus.ACTIVE
            )
            for i in range(3)
        ]
        
        # Mock database queries
        mock_db.query.return_value.options.return_value.join.return_value.filter.return_value.filter.return_value.count.return_value = len(mock_conversations)
        mock_db.query.return_value.options.return_value.join.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_conversations
        
        result_conversations, total_count = await service.search_conversations(
            user_id=mock_user.id,
            query="Test",
            limit=10,
            offset=0
        )
        
        assert len(result_conversations) == len(mock_conversations)
        assert total_count == len(mock_conversations)
    
    def test_user_mentions_search(self, mock_db, mock_user):
        """Test user mentions/autocomplete functionality"""
        service = ConversationService(mock_db)
        
        mock_users = [
            User(
                id=f"user-{i}",
                username=f"testuser{i}",
                email=f"test{i}@example.com",
                first_name=f"Test{i}",
                last_name="User",
                is_active=True
            )
            for i in range(5)
        ]
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = mock_users
        
        result_users = await service.get_user_mentions(
            user_id=mock_user.id,
            query="test",
            limit=10
        )
        
        assert len(result_users) == len(mock_users)
        assert all("id" in user for user in result_users)
        assert all("username" in user for user in result_users)
        assert all("display_name" in user for user in result_users)
    
    def test_user_mentions_with_conversation_context(self, mock_db, mock_user, mock_conversation):
        """Test user mentions with conversation context (prioritize participants)"""
        service = ConversationService(mock_db)
        
        # Mock conversation participants
        participant_users = [
            User(
                id=f"participant-{i}",
                username=f"participant{i}",
                email=f"participant{i}@example.com",
                first_name=f"Participant{i}",
                last_name="User",
                is_active=True
            )
            for i in range(3)
        ]
        
        mock_conversation.participants = participant_users
        
        # Mock service method to return conversation
        with patch.object(service, 'get_conversation', return_value=mock_conversation):
            # Mock database queries for participants
            mock_db.query.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = participant_users
            
            result_users = await service.get_user_mentions(
                user_id=mock_user.id,
                query="participant",
                conversation_id=mock_conversation.id,
                limit=10
            )
            
            assert len(result_users) == len(participant_users)
            assert all(user["is_participant"] for user in result_users)

class TestInfiniteScroll:
    """Test infinite scroll functionality"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        return User(
            id="test-user-id",
            username="testuser",
            email="test@example.com",
            is_active=True
        )
    
    def test_get_conversation_messages_with_pagination(self, mock_db, mock_user):
        """Test getting conversation messages with pagination"""
        service = ConversationService(mock_db)
        
        # Create mock messages
        mock_messages = [
            Message(
                id=f"msg-{i}",
                conversation_id="test-conversation-id",
                sender_id="test-user-id",
                content=f"Message {i}",
                message_type=MessageType.CHAT,
                created_at=datetime.utcnow() - timedelta(minutes=i)
            )
            for i in range(50)
        ]
        
        # Mock conversation access
        mock_conversation = Conversation(
            id="test-conversation-id",
            title="Test Conversation",
            participants=[mock_user]
        )
        
        with patch.object(service, 'get_conversation', return_value=mock_conversation):
            # Mock database queries
            mock_db.query.return_value.options.return_value.filter.return_value.filter.return_value.count.return_value = len(mock_messages)
            mock_db.query.return_value.options.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_messages[:25]
            
            result_messages, total_count = await service.get_conversation_messages(
                conversation_id="test-conversation-id",
                user_id=mock_user.id,
                limit=25,
                offset=0
            )
            
            assert len(result_messages) == 25
            assert total_count == len(mock_messages)
    
    def test_get_conversation_messages_with_cursor(self, mock_db, mock_user):
        """Test getting conversation messages with cursor-based pagination"""
        service = ConversationService(mock_db)
        
        # Create mock messages
        base_time = datetime.utcnow()
        mock_messages = [
            Message(
                id=f"msg-{i}",
                conversation_id="test-conversation-id",
                sender_id="test-user-id",
                content=f"Message {i}",
                message_type=MessageType.CHAT,
                created_at=base_time - timedelta(minutes=i)
            )
            for i in range(25, 50)  # Older messages
        ]
        
        # Mock conversation access
        mock_conversation = Conversation(
            id="test-conversation-id",
            title="Test Conversation",
            participants=[mock_user]
        )
        
        # Mock the before_message for cursor
        before_message = Message(
            id="msg-25",
            created_at=base_time - timedelta(minutes=25)
        )
        
        with patch.object(service, 'get_conversation', return_value=mock_conversation):
            # Mock database queries
            mock_db.query.return_value.filter.return_value.first.return_value = before_message
            mock_db.query.return_value.options.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = len(mock_messages)
            mock_db.query.return_value.options.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_messages
            
            result_messages, total_count = await service.get_conversation_messages(
                conversation_id="test-conversation-id",
                user_id=mock_user.id,
                limit=25,
                offset=0,
                before_message_id="msg-25"
            )
            
            assert len(result_messages) == len(mock_messages)
            assert total_count == len(mock_messages)

class TestSearchAPI:
    """Test search API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        # Mock JWT token for testing
        return {"Authorization": "Bearer test-token"}
    
    def test_search_messages_endpoint(self, client):
        """Test message search API endpoint"""
        with patch('api.conversation_api.get_current_active_user') as mock_auth:
            mock_user = User(id="test-user", username="testuser", is_active=True)
            mock_auth.return_value = mock_user
            
            with patch('api.conversation_api.ConversationService') as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service
                
                # Mock search results
                mock_messages = [
                    Mock(
                        id="msg-1",
                        conversation_id="conv-1",
                        sender_id="user-1",
                        content="Test message",
                        message_type=MessageType.CHAT,
                        sender=Mock(username="testuser"),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        is_delivered=True,
                        is_read=True,
                        is_edited=False,
                        is_deleted=False
                    )
                ]
                
                mock_service.search_messages.return_value = (mock_messages, 1)
                
                response = client.get(
                    "/api/conversations/search/messages?query=test&limit=10&offset=0"
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "messages" in data
                assert "total_count" in data
                assert "has_more" in data
                assert len(data["messages"]) == 1
    
    def test_search_conversations_endpoint(self, client):
        """Test conversation search API endpoint"""
        with patch('api.conversation_api.get_current_active_user') as mock_auth:
            mock_user = User(id="test-user", username="testuser", is_active=True)
            mock_auth.return_value = mock_user
            
            with patch('api.conversation_api.ConversationService') as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service
                
                # Mock search results
                mock_conversations = [
                    Mock(
                        id="conv-1",
                        title="Test Conversation",
                        is_group=False,
                        participants=[],
                        messages=[],
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        last_message_at=datetime.utcnow(),
                        status=ConversationStatus.ACTIVE,
                        created_by="test-user",
                        is_archived=False,
                        is_muted=False
                    )
                ]
                
                mock_service.search_conversations.return_value = (mock_conversations, 1)
                
                response = client.get(
                    "/api/conversations/search/conversations?query=test&limit=10&offset=0"
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "conversations" in data
                assert "total_count" in data
                assert "has_more" in data
                assert len(data["conversations"]) == 1
    
    def test_user_mentions_endpoint(self, client):
        """Test user mentions API endpoint"""
        with patch('api.conversation_api.get_current_active_user') as mock_auth:
            mock_user = User(id="test-user", username="testuser", is_active=True)
            mock_auth.return_value = mock_user
            
            with patch('api.conversation_api.ConversationService') as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service
                
                # Mock user mentions
                mock_users = [
                    {
                        "id": "user-1",
                        "username": "testuser1",
                        "display_name": "Test User 1",
                        "email": "test1@example.com",
                        "is_participant": True
                    }
                ]
                
                mock_service.get_user_mentions.return_value = mock_users
                
                response = client.get(
                    "/api/conversations/mentions/users?query=test&limit=10"
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "users" in data
                assert "query" in data
                assert len(data["users"]) == 1
                assert data["users"][0]["username"] == "testuser1"

class TestEnhancedChatInterface:
    """Test enhanced chat interface endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_enhanced_chat_with_search_endpoint(self, client):
        """Test enhanced chat with search interface endpoint"""
        with patch('api.enhanced_chat_api.get_current_active_user') as mock_auth:
            mock_user = User(id="test-user", username="testuser", is_active=True)
            mock_auth.return_value = mock_user
            
            with patch('api.enhanced_chat_api.ConversationService') as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service
                
                # Mock conversations
                mock_conversations = []
                mock_service.get_user_conversations.return_value = (mock_conversations, 0)
                
                response = client.get("/chat/search")
                
                assert response.status_code == 200
                assert "text/html" in response.headers["content-type"]

if __name__ == "__main__":
    pytest.main([__file__])