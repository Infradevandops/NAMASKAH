# WebSocket Real-time Updates Manager
import asyncio
import json
import jwt
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, str] = {}  # user_id -> connection_id
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and store user mapping"""
        await websocket.accept()
        connection_id = f"conn_{datetime.now(timezone.utc).timestamp()}"
        self.active_connections[connection_id] = websocket
        self.user_connections[user_id] = connection_id
        print(f"✅ WebSocket connected: {user_id}")
        
        # Send connection confirmation
        await self.send_personal_message({
            "type": "connection_established",
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, user_id)
        
    def disconnect(self, user_id: str):
        """Remove user connection"""
        connection_id = self.user_connections.get(user_id)
        if connection_id and connection_id in self.active_connections:
            del self.active_connections[connection_id]
            del self.user_connections[user_id]
            print(f"❌ WebSocket disconnected: {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        connection_id = self.user_connections.get(user_id)
        if connection_id and connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
                return True
            except Exception as e:
                print(f"Failed to send message to {user_id}: {e}")
                self.disconnect(user_id)
                return False
        return False
    
    async def broadcast(self, message: dict):
        """Send message to all connected users"""
        disconnected = []
        for user_id, connection_id in self.user_connections.items():
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception:
                    disconnected.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected:
            self.disconnect(user_id)
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if user is connected"""
        return user_id in self.user_connections

# Global connection manager
manager = ConnectionManager()

async def handle_websocket_message(websocket: WebSocket, user_id: str, data: dict, db: Session):
    """Handle incoming WebSocket messages"""
    message_type = data.get("type")
    
    if message_type == "ping":
        # Respond to heartbeat
        await websocket.send_text(json.dumps({"type": "pong"}))
        
    elif message_type == "subscribe_verification":
        # Subscribe to verification updates
        verification_id = data.get("verification_id")
        if verification_id:
            # Store subscription (in production, use Redis or database)
            await websocket.send_text(json.dumps({
                "type": "subscribed",
                "verification_id": verification_id
            }))
    
    elif message_type == "unsubscribe_verification":
        # Unsubscribe from verification updates
        verification_id = data.get("verification_id")
        if verification_id:
            await websocket.send_text(json.dumps({
                "type": "unsubscribed", 
                "verification_id": verification_id
            }))
    
    elif message_type == "get_status":
        # Send current status
        await websocket.send_text(json.dumps({
            "type": "status",
            "connected_users": manager.get_connection_count(),
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))

async def notify_verification_update(verification_id: str, user_id: str, status: str, phone_number: str = None):
    """Notify user of verification status update"""
    message = {
        "type": "verification_update",
        "verification_id": verification_id,
        "status": status,
        "phone_number": phone_number,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.send_personal_message(message, user_id)

async def notify_sms_received(verification_id: str, user_id: str, sms_content: str, sender: str = None):
    """Notify user of new SMS message"""
    message = {
        "type": "sms_received",
        "verification_id": verification_id,
        "message": sms_content,
        "sender": sender or "Unknown",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.send_personal_message(message, user_id)

async def notify_low_balance(user_id: str, current_balance: float, threshold: float = 1.0):
    """Notify user of low balance"""
    if current_balance <= threshold:
        message = {
            "type": "low_balance_warning",
            "current_balance": current_balance,
            "threshold": threshold,
            "message": f"Your balance is low (N{current_balance}). Please fund your wallet.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await manager.send_personal_message(message, user_id)

async def notify_payment_received(user_id: str, amount: float, new_balance: float, reference: str):
    """Notify user of successful payment"""
    message = {
        "type": "payment_received",
        "amount": amount,
        "new_balance": new_balance,
        "reference": reference,
        "message": f"Payment of N{amount} received. New balance: N{new_balance}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.send_personal_message(message, user_id)

async def notify_rental_expiring(user_id: str, rental_id: str, phone_number: str, expires_in_minutes: int):
    """Notify user of rental expiring soon"""
    message = {
        "type": "rental_expiring",
        "rental_id": rental_id,
        "phone_number": phone_number,
        "expires_in_minutes": expires_in_minutes,
        "message": f"Rental {phone_number} expires in {expires_in_minutes} minutes",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.send_personal_message(message, user_id)

async def broadcast_system_announcement(title: str, message: str, type: str = "info"):
    """Broadcast system-wide announcement"""
    announcement = {
        "type": "system_announcement",
        "title": title,
        "message": message,
        "announcement_type": type,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast(announcement)

def add_websocket_routes(app):
    """Add WebSocket routes to FastAPI app"""
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket, token: str = None):
        """Main WebSocket endpoint with authentication"""
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        try:
            # Verify JWT token
            from security_patches import validate_token
            import os
            JWT_SECRET = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
            
            payload = validate_token(token, JWT_SECRET)
            if not payload:
                await websocket.close(code=4001, reason="Invalid token")
                return
            
            user_id = payload.get("user_id")
            if not user_id:
                await websocket.close(code=4001, reason="Invalid user")
                return
            
            # Connect user
            await manager.connect(websocket, user_id)
            
            try:
                while True:
                    # Listen for messages
                    data = await websocket.receive_text()
                    try:
                        message_data = json.loads(data)
                        # Handle message (would need db session in production)
                        await handle_websocket_message(websocket, user_id, message_data, None)
                    except json.JSONDecodeError:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Invalid JSON format"
                        }))
                        
            except WebSocketDisconnect:
                manager.disconnect(user_id)
                
        except Exception as e:
            print(f"WebSocket error: {e}")
            await websocket.close(code=4000, reason="Server error")
    
    @app.websocket("/ws/verification/{verification_id}")
    async def verification_websocket(websocket: WebSocket, verification_id: str, token: str = None):
        """WebSocket endpoint for specific verification updates"""
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        try:
            # Verify token and get user
            from security_patches import validate_token
            import os
            JWT_SECRET = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
            
            payload = validate_token(token, JWT_SECRET)
            if not payload:
                await websocket.close(code=4001, reason="Invalid token")
                return
            
            user_id = payload.get("user_id")
            await websocket.accept()
            
            # Send initial status
            await websocket.send_text(json.dumps({
                "type": "connected",
                "verification_id": verification_id,
                "user_id": user_id
            }))
            
            # Keep connection alive and listen for updates
            try:
                while True:
                    # In production, this would check for new messages periodically
                    await asyncio.sleep(5)
                    
                    # Send heartbeat
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }))
                    
            except WebSocketDisconnect:
                print(f"Verification WebSocket disconnected: {verification_id}")
                
        except Exception as e:
            print(f"Verification WebSocket error: {e}")
            await websocket.close(code=4000, reason="Server error")

# Background task to check for SMS updates
async def sms_checker_task():
    """Background task to check for new SMS messages"""
    while True:
        try:
            # In production, this would:
            # 1. Get all active verifications
            # 2. Check TextVerified API for new messages
            # 3. Notify users via WebSocket
            # 4. Update database
            
            await asyncio.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            print(f"SMS checker error: {e}")
            await asyncio.sleep(30)  # Wait longer on error

# Export manager and functions
__all__ = [
    'manager',
    'add_websocket_routes',
    'notify_verification_update',
    'notify_sms_received', 
    'notify_low_balance',
    'notify_payment_received',
    'notify_rental_expiring',
    'broadcast_system_announcement',
    'sms_checker_task'
]