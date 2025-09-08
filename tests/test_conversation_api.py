#!/usr/bin/env python3
"""
Integration tests for Conversation API endpoints
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import get_db
from models import Base, User, Conversation, Message, ConversationStatus, MessageType
from auth.security import hash_password, create_access_token

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_conversation_api.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

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
def auth_headers(test_users):
    """Create authentication headers for test users"""
    headers = {}
    for i, user in enumerate(test_users):
        token = create_access_token({"sub": user.id, "email": user.email})
        headers[f"user{i}"] = {"Authorization": f"Bearer {token}"}
    return headers

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

class TestConversationEndpoints:
    """Test conversation CRUD endpoints"""
    
    def test_create_conversation(self, client, test_users, auth_headers, db_session):
        """Test creating a conversation"""
        response = client.post(
            "/api/conversations/",
            json={
                "title": "Test Conversation",
                "is_group": False,
                "participant_ids": [test_users[1].id]
            },
            headers=auth_headers["user0"]
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Conversation"
        assert data["is_group"] is False
        assert data["participant_count"] == 2  # Creator + participant    
   
 def test_get_conversations(self, client, test_users, auth_headers, db_session):
        """Test getting user conversations"""
        # Create a conversation first
        client.post(
            "/api/conversations/",
            json={
                "title": "Test Get Conversations",
                "participant_ids": [test_users[1].id]
            },
            headers=auth_headers["user0"]
        )
        
        # Get conversations
        response = client.get(
            "/api/conversations/",
            headers=auth_headers["user0"]
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 1
        assert len(data["conversations"]) >= 1
        assert data["conversations"][0]["title"] == "Test Get Conversations"
    
    def test_get_conversation_by_id(self, client, test_users, auth_headers, db_session):
        """Test getting specific conversation"""
        # Create conversation
        create_response = client.post(
            "/api/conversations/",
            json={
                "title": "Specific Conversation",
                "participant_ids": [test_users[1].id]
            },
            headers=auth_headers["user0"]
        )
        
        conversation_id = create_response.json()["id"]
        
        # Get specific conversation
        response = client.get(
            f"/api/conversations/{conversation_id}",
            headers=auth_headers["user0"]
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation_id
        assert data["title"] == "Specific Conversation"
    
    def test_update_conversation(self, client, test_users, auth_headers, db_session):
        """Test updating conversation"""
        # Create conversation
        create_response = client.post(
            "/api/conversations/",
            json={"title": "Original Title"},
            headers=auth_headers["user0"]
        )
        
        conversation_id = create_response.json()["id"]
        
        # Update conversation
        response = client.put(
            f"/api/conversations/{conversation_id}",
            json={
                "title": "Updated Title",
                "is_archived": True
            },
            headers=auth_headers["user0"]
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["is_archived"] is True
    
    def test_delete_conversation(self, client, test_users, auth_headers, db_session):
        """Test deleting conversation"""
        # Create conversation
        create_response = client.post(
            "/api/conversations/",
            json={"title": "To Delete"},
            headers=auth_headers["user0"]
        )
        
        conversation_id = create_response.json()["id"]
        
        # Delete conversation
        response = client.delete(
            f"/api/conversations/{conversation_id}",
            headers=auth_headers["user0"]
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

class TestMessageEndpoints:
    """Test message endpoints"""
    
    def test_send_message(self, client, test_users, auth_headers, db_session):
        """Test sending a message"""
        # Create conversation
        create_response = client.post(
            "/api/conversations/",
            json={
                "title": "Message Test",
                "participant_ids": [test_users[1].id]
            },
            headers=auth_headers["user0"]
        )
        
        conversation_id = create_response.json()["id"]
        
        # Send message
        response = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={
                "content": "Hello, world!",
                "message_type": "CHAT"
            },
            headers=auth_headers["user0"]
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Hello, world!"
        assert data["message_type"] == "CHAT"
        assert data["sender_id"] == test_users[0].id
    
    def test_get_messages(self, client, test_users, auth_headers, db_session):
        """Test getting conversation messages"""
        # Create conversation
        create_response = client.post(
            "/api/conversations/",
            json={
                "title": "Get Messages Test",
                "participant_ids": [test_users[1].id]
            },
            headers=auth_headers["user0"]
        )
        
        conversation_id = create_response.json()["id"]
        
        # Send multiple messages
        for i in range(3):
            client.post(
                f"/api/conversations/{conversation_id}/messages",
                json={"content": f"Message {i}"},
                headers=auth_headers["user0"]
            )
        
        # Get messages
        response = client.get(
            f"/api/conversations/{conversation_id}/messages",
            headers=auth_headers["user0"]
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 3
        assert len(data["messages"]) == 3
    
    def test_update_message(self, client, test_users, auth_headers, db_session):
        """Test updating a message"""
        # Create conversation and message
        create_response = client.post(
            "/api/conversations/",
            json={"title": "Update Message Test"},
            headers=auth_headers["user0"]
        )
        
        conversation_id = create_response.json()["id"]
        
        message_response = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"content": "Original content"},
            headers=auth_headers["user0"]
        )
        
        message_id = message_response.json()["id"]
        
        # Update message
        response = client.put(
            f"/api/conversations/{conversation_id}/messages/{message_id}",
            json={"content": "Updated content"},
            headers=auth_headers["user0"]
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["is_edited"] is True
    
    def test_delete_message(self, client, test_users, auth_headers, db_session):
        """Test deleting a message"""
        # Create conversation and message
        create_response = client.post(
            "/api/conversations/",
            json={"title": "Delete Message Test"},
            headers=auth_headers["user0"]
        )
        
        conversation_id = create_response.json()["id"]
        
        message_response = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"content": "To be deleted"},
            headers=auth_headers["user0"]
        )
        
        message_id = message_response.json()["id"]
        
        # Delete message
        response = client.delete(
            f"/api/conversations/{conversation_id}/messages/{message_id}",
            headers=auth_headers["user0"]
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

class TestUtilityEndpoints:
    """Test utility endpoints"""
    
    def test_mark_messages_as_read(self, client, test_users, auth_headers, db_session):
        """Test marking messages as read"""
        # Create conversation
        create_response = client.post(
            "/api/conversations/",
            json={
                "title": "Read Test",
                "participant_ids": [test_users[1].id]
            },
            headers=auth_headers["user0"]
        )
        
        conversation_id = create_response.json()["id"]
        
        # Send messages from user0
        for i in range(3):
            client.post(
                f"/api/conversations/{conversation_id}/messages",
                json={"content": f"Message {i}"},
                headers=auth_headers["user0"]
            )
        
        # Mark as read by user1
        response = client.post(
            f"/api/conversations/{conversation_id}/messages/mark-read",
            headers=auth_headers["user1"]
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["marked_count"] == 3
    
    def test_search_messages(self, client, test_users, auth_headers, db_session):
        """Test searching messages"""
        # Create conversation
        create_response = client.post(
            "/api/conversations/",
            json={
                "title": "Search Test",
                "participant_ids": [test_users[1].id]
            },
            headers=auth_headers["user0"]
        )
        
        conversation_id = create_response.json()["id"]
        
        # Send messages with different content
        messages = ["Hello world", "Python is great", "Hello Python"]
        for content in messages:
            client.post(
                f"/api/conversations/{conversation_id}/messages",
                json={"content": content},
                headers=auth_headers["user0"]
            )
        
        # Search for "Hello"
        response = client.get(
            "/api/conversations/search/messages?query=Hello",
            headers=auth_headers["user0"]
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert all("Hello" in msg["content"] for msg in data["messages"])

class TestAuthenticationAndAuthorization:
    """Test authentication and authorization"""
    
    def test_unauthorized_access(self, client, db_session):
        """Test accessing endpoints without authentication"""
        response = client.get("/api/conversations/")
        assert response.status_code == 401
    
    def test_access_other_user_conversation(self, client, test_users, auth_headers, db_session):
        """Test accessing conversation user is not part of"""
        # Create conversation with user0 only
        create_response = client.post(
            "/api/conversations/",
            json={"title": "Private Conversation"},
            headers=auth_headers["user0"]
        )
        
        conversation_id = create_response.json()["id"]
        
        # Try to access with user2 (not a participant)
        response = client.get(
            f"/api/conversations/{conversation_id}",
            headers=auth_headers["user2"]
        )
        
        assert response.status_code == 404

class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_invalid_conversation_id(self, client, auth_headers):
        """Test accessing non-existent conversation"""
        response = client.get(
            "/api/conversations/invalid-id",
            headers=auth_headers["user0"]
        )
        
        assert response.status_code == 404
    
    def test_invalid_message_data(self, client, test_users, auth_headers, db_session):
        """Test sending message with invalid data"""
        # Create conversation
        create_response = client.post(
            "/api/conversations/",
            json={"title": "Error Test"},
            headers=auth_headers["user0"]
        )
        
        conversation_id = create_response.json()["id"]
        
        # Send message without content
        response = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"message_type": "CHAT"},  # Missing content
            headers=auth_headers["user0"]
        )
        
        assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])