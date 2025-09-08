#!/usr/bin/env python3
"""
Unit tests for Enhanced WebSocket Manager
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base, User, Conversation, Message, MessageType, ConversationStatus
from services.websocket_manager import AuthenticatedConnectionManager, AuthenticatedWebSocketHandler
from auth.security import hash_password, create_access_token

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_websocket.db"
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

@pytest.fixture
def test_conversation(db_session, test_users):
    """Create a test conversation"""
    conversation = Conversation(
        title="Test Conversation",
        created_by=test_users[0].id,
        status=ConversationStatus.ACTIVE
    )
    
    conversation.participants.extend(test_users[:2])
    
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    
    return conversation

@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket"""
    websocket = Mock()
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.close = AsyncMock()
    websocket.receive_text = AsyncMock()
    return websocket

@pytest.fixture
def connection_manager():
    """Create connection manager instance"""
    return AuthenticatedConnectionManager()

@pytest.fixture
def websocket_handler(connection_manager):
    """Create WebSocket handler instance"""
    return AuthenticatedWebSocketHandler(connection_manager)

class TestAuthenticatedConnectionManager:
    """Test authenticated connection manager"""
    
    @pytest.mark.asyncio
    async def test_authenticate_valid_token(self, connection_manager, mock_websocket, test_users):
        """Test successful authentication with valid token"""
        user = test_users[0]
        token = create_access_token({"sub": user.id, "email": user.email})
        
        with patch('services.websocket_manager.SessionLocal', return_value=Mock()):
            with patch.object(connection_manager, '_load_user_conversations', new_callable=AsyncMock):
                with patch.object(connection_manager, '_update_user_presence', new_callable=AsyncMock):
                    with patch.object(connection_manager, 'broadcast_user_status', new_callable=AsyncMock):
                        with patch.object(connection_manager, '_get_user_online_contacts', new_callable=AsyncMock, return_value=[]):
                            user_id = await connection_manager.authenticate_and_connect(mock_websocket, token)
        
        assert user_id == user.id
        assert user.id in connection_manager.active_connections
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_invalid_token(self, connection_manager, mock_websocket):
        """Test authentication failure with invalid token"""
        invalid_token = "invalid.jwt.token"
        
        user_id = await connection_manager.authenticate_and_connect(mock_websocket, invalid_token)
        
        assert user_id is None
        mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self, connection_manager, mock_websocket, test_users):
        """Test sending personal message to connected user"""
        user = test_users[0]
        
        # Manually add user to connections for testing
        from services.websocket_manager import UserPresence
        presence = UserPresence(user.id, mock_websocket, datetime.utcnow())
        connection_manager.active_connections[user.id] = presence
        
        message = {"type": "test", "content": "Hello"}
        result = await connection_manager.send_personal_message(user.id, message)
        
        assert result is True
        mock_websocket.send_text.assert_called_once_with(json.dumps(message))
    
    @pytest.mark.asyncio
    async def test_send_to_conversation(self, connection_manager, mock_websocket, test_users, test_conversation):
        """Test sending message to conversation participants"""
        user1, user2 = test_users[:2]
        
        # Add users to connections
        from services.websocket_manager import UserPresence
        presence1 = UserPresence(user1.id, mock_websocket, datetime.utcnow())
        presence2 = UserPresence(user2.id, Mock(), datetime.utcnow())
        presence2.websocket.send_text = AsyncMock()
        
        connection_manager.active_connections[user1.id] = presence1
        connection_manager.active_connections[user2.id] = presence2
        
        # Mock conversation participants
        with patch.object(connection_manager, '_get_conversation_participants', 
                         new_callable=AsyncMock, return_value={user1.id, user2.id}):
            
            message = {"type": "test", "content": "Hello conversation"}
            sent_count = await connection_manager.send_to_conversation(
                test_conversation.id, message, exclude_user=user1.id
            )
        
        assert sent_count == 1  # Only user2 should receive (user1 excluded)
    
    @pytest.mark.asyncio
    async def test_join_conversation(self, connection_manager, mock_websocket, test_users, test_conversation):
        """Test joining a conversation"""
        user = test_users[0]
        
        # Add user to connections
        from services.websocket_manager import UserPresence
        presence = UserPresence(user.id, mock_websocket, datetime.utcnow())
        connection_manager.active_connections[user.id] = presence
        
        with patch.object(connection_manager, '_verify_conversation_access', 
                         new_callable=AsyncMock, return_value=True):
            with patch.object(connection_manager, 'send_to_conversation', new_callable=AsyncMock):
                
                result = await connection_manager.join_conversation(user.id, test_conversation.id)
        
        assert result is True
        assert test_conversation.id in presence.conversations
        assert test_conversation.id in connection_manager.conversation_participants
        assert user.id in connection_manager.conversation_participants[test_conversation.id]
    
    @pytest.mark.asyncio
    async def test_handle_typing_indicator(self, connection_manager, test_users, test_conversation):
        """Test typing indicator handling"""
        user = test_users[0]
        
        with patch.object(connection_manager, 'send_to_conversation', new_callable=AsyncMock) as mock_send:
            await connection_manager.handle_typing_indicator(user.id, test_conversation.id, True)
        
        # Check typing users tracking
        assert test_conversation.id in connection_manager.typing_users
        assert user.id in connection_manager.typing_users[test_conversation.id]
        
        # Verify message was sent to conversation
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == test_conversation.id  # conversation_id
        assert call_args[1]['exclude_user'] == user.id
        
        message = call_args[0][1]
        assert message['type'] == 'typing_indicator'
        assert message['is_typing'] is True
    
    def test_disconnect(self, connection_manager, mock_websocket, test_users):
        """Test user disconnection"""
        user = test_users[0]
        
        # Add user to connections
        from services.websocket_manager import UserPresence
        presence = UserPresence(user.id, mock_websocket, datetime.utcnow())
        presence.conversations.add("conv1")
        connection_manager.active_connections[user.id] = presence
        connection_manager.conversation_participants["conv1"] = {user.id}
        connection_manager.typing_users["conv1"] = {user.id}
        
        with patch.object(connection_manager, '_update_user_presence', new_callable=AsyncMock):
            connection_manager.disconnect(user.id)
        
        # Verify cleanup
        assert user.id not in connection_manager.active_connections
        assert user.id not in connection_manager.conversation_participants["conv1"]
        assert user.id not in connection_manager.typing_users["conv1"]
    
    def test_get_online_users(self, connection_manager, mock_websocket, test_users):
        """Test getting online users list"""
        user1, user2 = test_users[:2]
        
        # Add users to connections
        from services.websocket_manager import UserPresence
        presence1 = UserPresence(user1.id, mock_websocket, datetime.utcnow())
        presence2 = UserPresence(user2.id, Mock(), datetime.utcnow())
        
        connection_manager.active_connections[user1.id] = presence1
        connection_manager.active_connections[user2.id] = presence2
        
        online_users = connection_manager.get_online_users()
        
        assert len(online_users) == 2
        assert user1.id in online_users
        assert user2.id in online_users
    
    def test_is_user_online(self, connection_manager, mock_websocket, test_users):
        """Test checking if user is online"""
        user = test_users[0]
        
        # User not connected
        assert connection_manager.is_user_online(user.id) is False
        
        # Add user to connections
        from services.websocket_manager import UserPresence
        presence = UserPresence(user.id, mock_websocket, datetime.utcnow())
        connection_manager.active_connections[user.id] = presence
        
        # User connected
        assert connection_manager.is_user_online(user.id) is True

class TestAuthenticatedWebSocketHandler:
    """Test authenticated WebSocket handler"""
    
    @pytest.mark.asyncio
    async def test_handle_websocket_success(self, websocket_handler, mock_websocket, test_users):
        """Test successful WebSocket handling"""
        user = test_users[0]
        token = create_access_token({"sub": user.id, "email": user.email})
        
        # Mock the connection manager methods
        with patch.object(websocket_handler.connection_manager, 'authenticate_and_connect', 
                         new_callable=AsyncMock, return_value=user.id):
            with patch.object(websocket_handler.connection_manager, 'disconnect'):
                
                # Mock WebSocket to raise disconnect after one message
                mock_websocket.receive_text.side_effect = [
                    json.dumps({"type": "ping"}),
                    Exception("WebSocketDisconnect")  # Simulate disconnect
                ]
                
                with patch.object(websocket_handler, 'process_message', new_callable=AsyncMock):
                    try:
                        await websocket_handler.handle_websocket(mock_websocket, token)
                    except:
                        pass  # Expected due to simulated disconnect
    
    @pytest.mark.asyncio
    async def test_process_ping_message(self, websocket_handler, test_users):
        """Test processing ping message"""
        user = test_users[0]
        
        with patch.object(websocket_handler.connection_manager, 'send_personal_message', 
                         new_callable=AsyncMock) as mock_send:
            
            await websocket_handler.process_message(user.id, {"type": "ping"})
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == user.id
        message = call_args[0][1]
        assert message['type'] == 'pong'
    
    @pytest.mark.asyncio
    async def test_process_typing_message(self, websocket_handler, test_users):
        """Test processing typing indicator message"""
        user = test_users[0]
        conversation_id = "test_conv_id"
        
        with patch.object(websocket_handler.connection_manager, 'handle_typing_indicator', 
                         new_callable=AsyncMock) as mock_typing:
            
            message = {
                "type": "typing",
                "conversation_id": conversation_id,
                "is_typing": True
            }
            
            await websocket_handler.process_message(user.id, message)
        
        mock_typing.assert_called_once_with(user.id, conversation_id, True)
    
    @pytest.mark.asyncio
    async def test_process_join_conversation(self, websocket_handler, test_users):
        """Test processing join conversation message"""
        user = test_users[0]
        conversation_id = "test_conv_id"
        
        with patch.object(websocket_handler.connection_manager, 'join_conversation', 
                         new_callable=AsyncMock, return_value=True) as mock_join:
            with patch.object(websocket_handler.connection_manager, 'send_personal_message', 
                             new_callable=AsyncMock) as mock_send:
                
                message = {
                    "type": "join_conversation",
                    "conversation_id": conversation_id
                }
                
                await websocket_handler.process_message(user.id, message)
        
        mock_join.assert_called_once_with(user.id, conversation_id)
        mock_send.assert_called_once()
        
        # Check response message
        call_args = mock_send.call_args
        response = call_args[0][1]
        assert response['type'] == 'conversation_joined'
        assert response['success'] is True
    
    @pytest.mark.asyncio
    async def test_process_get_online_users(self, websocket_handler, test_users):
        """Test processing get online users message"""
        user = test_users[0]
        online_users = [test_users[0].id, test_users[1].id]
        
        with patch.object(websocket_handler.connection_manager, 'get_online_users', 
                         return_value=online_users):
            with patch.object(websocket_handler.connection_manager, 'send_personal_message', 
                             new_callable=AsyncMock) as mock_send:
                
                await websocket_handler.process_message(user.id, {"type": "get_online_users"})
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        response = call_args[0][1]
        assert response['type'] == 'online_users'
        assert response['users'] == online_users
    
    @pytest.mark.asyncio
    async def test_process_unknown_message_type(self, websocket_handler, test_users):
        """Test processing unknown message type"""
        user = test_users[0]
        
        with patch.object(websocket_handler.connection_manager, 'send_personal_message', 
                         new_callable=AsyncMock) as mock_send:
            
            await websocket_handler.process_message(user.id, {"type": "unknown_type"})
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        response = call_args[0][1]
        assert response['type'] == 'error'
        assert 'Unknown message type' in response['message']

class TestWebSocketIntegration:
    """Test WebSocket integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_multiple_users_conversation(self, connection_manager, test_users, test_conversation):
        """Test multiple users in a conversation"""
        user1, user2 = test_users[:2]
        
        # Create mock WebSockets
        ws1 = Mock()
        ws1.send_text = AsyncMock()
        ws2 = Mock()
        ws2.send_text = AsyncMock()
        
        # Add users to connections
        from services.websocket_manager import UserPresence
        presence1 = UserPresence(user1.id, ws1, datetime.utcnow())
        presence2 = UserPresence(user2.id, ws2, datetime.utcnow())
        
        connection_manager.active_connections[user1.id] = presence1
        connection_manager.active_connections[user2.id] = presence2
        
        # Mock conversation participants
        with patch.object(connection_manager, '_get_conversation_participants', 
                         new_callable=AsyncMock, return_value={user1.id, user2.id}):
            
            # Send message to conversation
            message = {"type": "test_broadcast", "content": "Hello everyone"}
            sent_count = await connection_manager.send_to_conversation(
                test_conversation.id, message
            )
        
        assert sent_count == 2
        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_typing_indicator_flow(self, connection_manager, test_users, test_conversation):
        """Test complete typing indicator flow"""
        user1, user2 = test_users[:2]
        
        # Create mock WebSockets
        ws1 = Mock()
        ws1.send_text = AsyncMock()
        ws2 = Mock()
        ws2.send_text = AsyncMock()
        
        # Add users to connections
        from services.websocket_manager import UserPresence
        presence1 = UserPresence(user1.id, ws1, datetime.utcnow())
        presence2 = UserPresence(user2.id, ws2, datetime.utcnow())
        
        connection_manager.active_connections[user1.id] = presence1
        connection_manager.active_connections[user2.id] = presence2
        
        # Mock conversation participants
        with patch.object(connection_manager, '_get_conversation_participants', 
                         new_callable=AsyncMock, return_value={user1.id, user2.id}):
            
            # User1 starts typing
            await connection_manager.handle_typing_indicator(user1.id, test_conversation.id, True)
            
            # Verify user2 receives typing notification
            ws2.send_text.assert_called()
            call_args = ws2.send_text.call_args
            message_data = json.loads(call_args[0][0])
            assert message_data['type'] == 'typing_indicator'
            assert message_data['is_typing'] is True
            assert user1.id in message_data['typing_users']
            
            # User1 stops typing
            ws2.send_text.reset_mock()
            await connection_manager.handle_typing_indicator(user1.id, test_conversation.id, False)
            
            # Verify user2 receives stop typing notification
            ws2.send_text.assert_called()
            call_args = ws2.send_text.call_args
            message_data = json.loads(call_args[0][0])
            assert message_data['is_typing'] is False
            assert user1.id not in message_data['typing_users']

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])