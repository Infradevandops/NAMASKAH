#!/usr/bin/env python3
"""
Enhanced WebSocket Manager for Real-time Communication with Authentication
"""
import json
import asyncio
from typing import Dict, List, Set, Optional, Tuple
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import jwt

from database import SessionLocal
from models import User, Conversation, Message, conversation_participants
from auth.security import verify_token
from services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

class UserPresence:
    """User presence tracking model"""
    def __init__(self, user_id: str, websocket: WebSocket, last_seen: datetime):
        self.user_id = user_id
        self.websocket = websocket
        self.last_seen = last_seen
        self.conversations: Set[str] = set()  # Active conversations
        self.is_typing_in: Optional[str] = None  # Currently typing in conversation

class AuthenticatedConnectionManager:
    """Enhanced WebSocket connection manager with authentication and database integration"""
    
    def __init__(self):
        # Active connections: user_id -> UserPresence
        self.active_connections: Dict[str, UserPresence] = {}
        
        # Conversation participants: conversation_id -> set of user_ids
        self.conversation_participants: Dict[str, Set[str]] = {}
        
        # Typing indicators: conversation_id -> set of user_ids
        self.typing_users: Dict[str, Set[str]] = {}
        
        # Message delivery tracking: message_id -> set of user_ids (delivered to)
        self.message_delivery: Dict[str, Set[str]] = {}
    
    async def authenticate_and_connect(self, websocket: WebSocket, token: str) -> Optional[str]:
        """Authenticate WebSocket connection and return user_id if successful"""
        try:
            # Verify JWT token
            payload = verify_token(token, "access")
            if not payload:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token payload")
                return None
            
            # Verify user exists and is active
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
                if not user:
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found or inactive")
                    return None
            finally:
                db.close()
            
            # Accept connection
            await websocket.accept()
            
            # Disconnect existing connection if any
            if user_id in self.active_connections:
                try:
                    await self.active_connections[user_id].websocket.close()
                except:
                    pass
                self.disconnect(user_id)
            
            # Create user presence
            presence = UserPresence(user_id, websocket, datetime.utcnow())
            self.active_connections[user_id] = presence
            
            # Load user's conversations
            await self._load_user_conversations(user_id)
            
            # Update database presence
            await self._update_user_presence(user_id, True)
            
            logger.info(f"User {user_id} authenticated and connected via WebSocket")
            
            # Notify other users about online status
            await self.broadcast_user_status(user_id, "online")
            
            # Send initial data
            await self.send_personal_message(user_id, {
                "type": "connection_established",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "online_users": await self._get_user_online_contacts(user_id)
            })
            
            return user_id
            
        except Exception as e:
            logger.error(f"WebSocket authentication failed: {e}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Authentication failed")
            return None
    
    def disconnect(self, user_id: str):
        """Handle WebSocket disconnection"""
        if user_id not in self.active_connections:
            return
        
        presence = self.active_connections[user_id]
        
        # Remove from conversation participants
        for conversation_id in presence.conversations:
            if conversation_id in self.conversation_participants:
                self.conversation_participants[conversation_id].discard(user_id)
        
        # Remove from typing indicators
        for conversation_id in self.typing_users:
            self.typing_users[conversation_id].discard(user_id)
        
        # Clean up presence
        del self.active_connections[user_id]
        
        # Update database presence
        asyncio.create_task(self._update_user_presence(user_id, False))
        
        logger.info(f"User {user_id} disconnected from WebSocket")
        
        # Notify other users about offline status
        asyncio.create_task(self.broadcast_user_status(user_id, "offline"))
    
    async def send_personal_message(self, user_id: str, message: dict):
        """Send message to specific user"""
        if user_id in self.active_connections:
            try:
                presence = self.active_connections[user_id]
                presence.last_seen = datetime.utcnow()
                await presence.websocket.send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"Failed to send message to {user_id}: {e}")
                # Remove broken connection
                self.disconnect(user_id)
                return False
        return False
    
    async def send_to_conversation(self, conversation_id: str, message: dict, 
                                 exclude_user: str = None):
        """Send message to all online users in a conversation"""
        sent_count = 0
        
        # Get conversation participants from cache or database
        participants = await self._get_conversation_participants(conversation_id)
        
        for user_id in participants:
            if exclude_user and user_id == exclude_user:
                continue
            
            if user_id in self.active_connections:
                try:
                    message_with_conversation = {
                        **message,
                        "conversation_id": conversation_id
                    }
                    await self.send_personal_message(user_id, message_with_conversation)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send to {user_id}: {e}")
        
        return sent_count
    
    async def broadcast_user_status(self, user_id: str, status: str):
        """Broadcast user online/offline status"""
        message = {
            "type": "user_status",
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to all connected users except the user themselves
        for uid, websocket in self.active_connections.items():
            if uid != user_id:
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    self.disconnect(uid)
    
    async def handle_typing_indicator(self, user_id: str, conversation_id: str, is_typing: bool):
        """Handle typing indicators"""
        if conversation_id not in self.typing_users:
            self.typing_users[conversation_id] = set()
        
        if is_typing:
            self.typing_users[conversation_id].add(user_id)
        else:
            self.typing_users[conversation_id].discard(user_id)
        
        # Broadcast typing status to conversation participants
        message = {
            "type": "typing_indicator",
            "conversation_id": conversation_id,
            "user_id": user_id,
            "is_typing": is_typing,
            "typing_users": list(self.typing_users[conversation_id])
        }
        
        await self.send_to_conversation(conversation_id, message, exclude_user=user_id)
    
    async def handle_message_read(self, user_id: str, conversation_id: str, message_id: str):
        """Handle message read receipts"""
        message = {
            "type": "message_read",
            "conversation_id": conversation_id,
            "message_id": message_id,
            "read_by": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_to_conversation(conversation_id, message, exclude_user=user_id)
    
    async def join_conversation(self, user_id: str, conversation_id: str) -> bool:
        """Add user to conversation for real-time updates"""
        if user_id not in self.active_connections:
            return False
        
        # Verify user has access to conversation
        if not await self._verify_conversation_access(user_id, conversation_id):
            return False
        
        presence = self.active_connections[user_id]
        presence.conversations.add(conversation_id)
        
        # Add to conversation participants cache
        if conversation_id not in self.conversation_participants:
            self.conversation_participants[conversation_id] = set()
        self.conversation_participants[conversation_id].add(user_id)
        
        # Notify user joined
        await self.send_to_conversation(conversation_id, {
            "type": "user_joined_conversation",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_user=user_id)
        
        return True
    
    async def leave_conversation(self, user_id: str, conversation_id: str):
        """Remove user from conversation updates"""
        if user_id in self.active_connections:
            presence = self.active_connections[user_id]
            presence.conversations.discard(conversation_id)
        
        if conversation_id in self.conversation_participants:
            self.conversation_participants[conversation_id].discard(user_id)
        
        # Remove from typing if applicable
        if conversation_id in self.typing_users:
            self.typing_users[conversation_id].discard(user_id)
    
    async def broadcast_new_message(self, message: Message):
        """Broadcast new message to conversation participants"""
        message_data = {
            "type": "new_message",
            "message": {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "sender_id": message.sender_id,
                "content": message.content,
                "message_type": message.message_type.value,
                "created_at": message.created_at.isoformat(),
                "sender_username": message.sender.username if message.sender else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to conversation participants
        sent_count = await self.send_to_conversation(
            message.conversation_id, 
            message_data, 
            exclude_user=message.sender_id
        )
        
        # Track message delivery
        if message.id not in self.message_delivery:
            self.message_delivery[message.id] = set()
        
        # Mark as delivered to online users
        participants = await self._get_conversation_participants(message.conversation_id)
        for user_id in participants:
            if user_id != message.sender_id and user_id in self.active_connections:
                self.message_delivery[message.id].add(user_id)
        
        return sent_count
    
    async def handle_message_delivery(self, user_id: str, message_id: str):
        """Handle message delivery confirmation"""
        if message_id in self.message_delivery:
            self.message_delivery[message_id].add(user_id)
        
        # Update database
        await self._update_message_delivery(message_id, user_id)
        
        # Notify sender about delivery
        db = SessionLocal()
        try:
            message = db.query(Message).filter(Message.id == message_id).first()
            if message and message.sender_id:
                await self.send_personal_message(message.sender_id, {
                    "type": "message_delivered",
                    "message_id": message_id,
                    "delivered_to": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
        finally:
            db.close()
    
    def get_online_users(self) -> List[str]:
        """Get list of currently online users"""
        return list(self.active_connections.keys())
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if user is currently online"""
        return user_id in self.active_connections
    
    async def send_notification(self, user_id: str, notification: dict):
        """Send push notification to user"""
        message = {
            "type": "notification",
            "notification": notification,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_personal_message(user_id, message)
    
    # Helper methods
    
    async def _load_user_conversations(self, user_id: str):
        """Load user's conversations into cache"""
        db = SessionLocal()
        try:
            # Get user's conversations
            conversations = db.query(Conversation.id).join(
                conversation_participants
            ).filter(
                conversation_participants.c.user_id == user_id
            ).all()
            
            presence = self.active_connections[user_id]
            for conv in conversations:
                presence.conversations.add(conv.id)
                
                # Add to conversation participants cache
                if conv.id not in self.conversation_participants:
                    self.conversation_participants[conv.id] = set()
                self.conversation_participants[conv.id].add(user_id)
                
        finally:
            db.close()
    
    async def _get_conversation_participants(self, conversation_id: str) -> Set[str]:
        """Get conversation participants from cache or database"""
        if conversation_id in self.conversation_participants:
            return self.conversation_participants[conversation_id]
        
        # Load from database
        db = SessionLocal()
        try:
            participants = db.query(conversation_participants.c.user_id).filter(
                conversation_participants.c.conversation_id == conversation_id
            ).all()
            
            participant_ids = {p.user_id for p in participants}
            self.conversation_participants[conversation_id] = participant_ids
            return participant_ids
            
        finally:
            db.close()
    
    async def _verify_conversation_access(self, user_id: str, conversation_id: str) -> bool:
        """Verify user has access to conversation"""
        db = SessionLocal()
        try:
            conversation_service = ConversationService(db)
            conversation = await conversation_service.get_conversation(conversation_id, user_id)
            return conversation is not None
        finally:
            db.close()
    
    async def _get_user_online_contacts(self, user_id: str) -> List[str]:
        """Get list of user's contacts who are currently online"""
        participants = await self._get_conversation_participants("")  # This needs to be improved
        online_contacts = []
        
        for contact_id in participants:
            if contact_id != user_id and self.is_user_online(contact_id):
                online_contacts.append(contact_id)
        
        return online_contacts
    
    async def _update_user_presence(self, user_id: str, is_online: bool):
        """Update user presence in database"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.last_seen = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update user presence: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def _update_message_delivery(self, message_id: str, user_id: str):
        """Update message delivery status in database"""
        db = SessionLocal()
        try:
            message = db.query(Message).filter(Message.id == message_id).first()
            if message:
                message.is_delivered = True
                message.delivered_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update message delivery: {e}")
            db.rollback()
        finally:
            db.close()

# Global connection manager instance
connection_manager = AuthenticatedConnectionManager()

class AuthenticatedWebSocketHandler:
    """Enhanced WebSocket handler with authentication and conversation integration"""
    
    def __init__(self, connection_manager: AuthenticatedConnectionManager):
        self.connection_manager = connection_manager
    
    async def handle_websocket(self, websocket: WebSocket, token: str):
        """Main WebSocket handler with authentication"""
        # Authenticate connection
        user_id = await self.connection_manager.authenticate_and_connect(websocket, token)
        if not user_id:
            return  # Connection was closed due to auth failure
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process different message types
                await self.process_message(user_id, message)
                
        except WebSocketDisconnect:
            self.connection_manager.disconnect(user_id)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from user {user_id}: {e}")
            await self.connection_manager.send_personal_message(user_id, {
                "type": "error",
                "message": "Invalid JSON format"
            })
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
            self.connection_manager.disconnect(user_id)
    
    async def process_message(self, user_id: str, message: dict):
        """Process incoming WebSocket message"""
        message_type = message.get("type")
        
        try:
            if message_type == "ping":
                # Heartbeat
                await self.connection_manager.send_personal_message(user_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message_type == "typing":
                # Typing indicator
                conversation_id = message.get("conversation_id")
                is_typing = message.get("is_typing", False)
                
                if conversation_id:
                    await self.connection_manager.handle_typing_indicator(
                        user_id, conversation_id, is_typing
                    )
            
            elif message_type == "message_read":
                # Message read receipt
                conversation_id = message.get("conversation_id")
                message_id = message.get("message_id")
                
                if conversation_id and message_id:
                    await self.connection_manager.handle_message_read(
                        user_id, conversation_id, message_id
                    )
            
            elif message_type == "message_delivered":
                # Message delivery confirmation
                message_id = message.get("message_id")
                
                if message_id:
                    await self.connection_manager.handle_message_delivery(user_id, message_id)
            
            elif message_type == "send_message":
                # Send new message through conversation service
                conversation_id = message.get("conversation_id")
                content = message.get("content")
                message_type_enum = message.get("message_type", "CHAT")
                
                if conversation_id and content:
                    db = SessionLocal()
                    try:
                        conversation_service = ConversationService(db)
                        from models import MessageCreate, MessageType
                        
                        # Create message
                        message_data = MessageCreate(
                            content=content,
                            message_type=MessageType(message_type_enum)
                        )
                        
                        new_message = await conversation_service.send_message(
                            conversation_id, user_id, message_data
                        )
                        
                        # Broadcast to conversation participants
                        await self.connection_manager.broadcast_new_message(new_message)
                        
                        # Send confirmation back to sender
                        await self.connection_manager.send_personal_message(user_id, {
                            "type": "message_sent",
                            "success": True,
                            "message_id": new_message.id,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
                    except Exception as e:
                        logger.error(f"Failed to send message: {e}")
                        await self.connection_manager.send_personal_message(user_id, {
                            "type": "message_sent",
                            "success": False,
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    finally:
                        db.close()
            
            elif message_type == "join_conversation":
                # Join conversation for real-time updates
                conversation_id = message.get("conversation_id")
                if conversation_id:
                    success = await self.connection_manager.join_conversation(user_id, conversation_id)
                    await self.connection_manager.send_personal_message(user_id, {
                        "type": "conversation_joined",
                        "conversation_id": conversation_id,
                        "success": success,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            elif message_type == "leave_conversation":
                # Leave conversation
                conversation_id = message.get("conversation_id")
                if conversation_id:
                    await self.connection_manager.leave_conversation(user_id, conversation_id)
                    await self.connection_manager.send_personal_message(user_id, {
                        "type": "conversation_left",
                        "conversation_id": conversation_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            elif message_type == "get_online_users":
                # Get list of online users
                online_users = self.connection_manager.get_online_users()
                await self.connection_manager.send_personal_message(user_id, {
                    "type": "online_users",
                    "users": online_users,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self.connection_manager.send_personal_message(user_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
                
        except Exception as e:
            logger.error(f"Error processing message type {message_type}: {e}")
            await self.connection_manager.send_personal_message(user_id, {
                "type": "error",
                "message": "Failed to process message"
            })

# Create global handler instance
websocket_handler = AuthenticatedWebSocketHandler(connection_manager)