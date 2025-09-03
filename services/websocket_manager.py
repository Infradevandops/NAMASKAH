#!/usr/bin/env python3
"""
WebSocket Manager for Real-time Communication
"""
import json
import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time messaging"""
    
    def __init__(self):
        # Active connections: user_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        
        # User presence: user_id -> last_seen
        self.user_presence: Dict[str, datetime] = {}
        
        # Typing indicators: conversation_id -> set of user_ids
        self.typing_users: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        # Disconnect existing connection if any
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].close()
            except:
                pass
        
        self.active_connections[user_id] = websocket
        self.user_presence[user_id] = datetime.utcnow()
        
        logger.info(f"User {user_id} connected via WebSocket")
        
        # Notify other users about online status
        await self.broadcast_user_status(user_id, "online")
        
        # Send initial data
        await self.send_personal_message(user_id, {
            "type": "connection_established",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect(self, user_id: str):
        """Handle WebSocket disconnection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        if user_id in self.user_presence:
            del self.user_presence[user_id]
        
        # Remove from all typing indicators
        for conversation_id in self.typing_users:
            self.typing_users[conversation_id].discard(user_id)
        
        logger.info(f"User {user_id} disconnected from WebSocket")
        
        # Notify other users about offline status
        asyncio.create_task(self.broadcast_user_status(user_id, "offline"))
    
    async def send_personal_message(self, user_id: str, message: dict):
        """Send message to specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"Failed to send message to {user_id}: {e}")
                # Remove broken connection
                self.disconnect(user_id)
                return False
        return False
    
    async def send_to_conversation(self, conversation_id: str, message: dict, 
                                 exclude_user: str = None):
        """Send message to all users in a conversation"""
        # This would need to query the database to get conversation participants
        # For now, we'll implement a simple version
        sent_count = 0
        
        for user_id, websocket in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue
            
            try:
                message_with_conversation = {
                    **message,
                    "conversation_id": conversation_id
                }
                await websocket.send_text(json.dumps(message_with_conversation))
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send to {user_id}: {e}")
                self.disconnect(user_id)
        
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

# Global connection manager instance
connection_manager = ConnectionManager()

class WebSocketHandler:
    """Handles WebSocket message processing"""
    
    def __init__(self, connection_manager: ConnectionManager, messaging_service=None):
        self.connection_manager = connection_manager
        self.messaging_service = messaging_service
    
    async def handle_websocket(self, websocket: WebSocket, user_id: str):
        """Main WebSocket handler"""
        await self.connection_manager.connect(websocket, user_id)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process different message types
                await self.process_message(user_id, message)
                
        except WebSocketDisconnect:
            self.connection_manager.disconnect(user_id)
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
            self.connection_manager.disconnect(user_id)
    
    async def process_message(self, user_id: str, message: dict):
        """Process incoming WebSocket message"""
        message_type = message.get("type")
        
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
        
        elif message_type == "send_message":
            # Send new message
            if self.messaging_service:
                recipient_id = message.get("recipient_id")
                content = message.get("content")
                
                if recipient_id and content:
                    result = await self.messaging_service.send_internal_message(
                        user_id, recipient_id, content
                    )
                    
                    # Send confirmation back to sender
                    await self.connection_manager.send_personal_message(user_id, {
                        "type": "message_sent",
                        "success": result["success"],
                        "message_id": result.get("message_id"),
                        "error": result.get("error")
                    })
        
        elif message_type == "join_conversation":
            # Join conversation for real-time updates
            conversation_id = message.get("conversation_id")
            if conversation_id:
                # This could be used to track which conversations a user is actively viewing
                pass
        
        else:
            logger.warning(f"Unknown message type: {message_type}")

# Create global handler instance
websocket_handler = WebSocketHandler(connection_manager)