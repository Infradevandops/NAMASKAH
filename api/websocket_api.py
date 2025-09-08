#!/usr/bin/env python3
"""
WebSocket API endpoints for real-time communication
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from typing import Optional
import logging

from services.websocket_manager import websocket_handler, connection_manager
from services.auth_service import get_current_active_user
from models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

@router.websocket("/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT token for authentication")
):
    """
    WebSocket endpoint for real-time chat communication
    
    Authentication:
    - Pass JWT token as query parameter: /ws/chat?token=your_jwt_token
    - Or send token in first message: {"type": "auth", "token": "your_jwt_token"}
    """
    if not token:
        # Try to get token from first message
        await websocket.accept()
        try:
            import json
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "auth":
                token = message.get("token")
            else:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
                return
        except Exception:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication message")
            return
    
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
        return
    
    # Handle WebSocket connection with authentication
    await websocket_handler.handle_websocket(websocket, token)

@router.get("/status")
async def websocket_status(current_user: User = Depends(get_current_active_user)):
    """
    Get WebSocket connection status and online users
    """
    try:
        online_users = connection_manager.get_online_users()
        is_online = connection_manager.is_user_online(current_user.id)
        
        return {
            "user_id": current_user.id,
            "is_connected": is_online,
            "online_users_count": len(online_users),
            "online_users": online_users[:10],  # Limit for privacy
            "websocket_url": "/ws/chat"
        }
        
    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get WebSocket status"
        )

@router.post("/broadcast/{conversation_id}")
async def broadcast_to_conversation(
    conversation_id: str,
    message: dict,
    current_user: User = Depends(get_current_active_user)
):
    """
    Broadcast a message to all users in a conversation (admin/testing endpoint)
    """
    try:
        # Verify user has access to conversation
        from database import get_db
        from services.conversation_service import ConversationService
        
        db = next(get_db())
        conversation_service = ConversationService(db)
        
        conversation = await conversation_service.get_conversation(conversation_id, current_user.id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Broadcast message
        sent_count = await connection_manager.send_to_conversation(
            conversation_id, 
            {
                "type": "broadcast",
                "message": message,
                "from_user": current_user.id,
                "timestamp": "now"
            }
        )
        
        return {
            "success": True,
            "sent_to": sent_count,
            "conversation_id": conversation_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error broadcasting to conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast message"
        )

@router.get("/health")
async def websocket_health():
    """
    WebSocket service health check
    """
    online_count = len(connection_manager.get_online_users())
    
    return {
        "status": "healthy",
        "service": "websocket",
        "version": "1.1.0",
        "online_users": online_count,
        "features": [
            "jwt_authentication",
            "real_time_messaging",
            "typing_indicators", 
            "presence_tracking",
            "message_delivery",
            "conversation_broadcasting"
        ]
    }

# WebSocket connection test page
@router.get("/test", response_class=HTMLResponse)
async def websocket_test_page():
    """
    Simple WebSocket test page for development
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            #messages { border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; margin: 10px 0; }
            input, button { margin: 5px; padding: 5px; }
            .message { margin: 5px 0; padding: 5px; background: #f0f0f0; }
            .error { color: red; }
            .success { color: green; }
        </style>
    </head>
    <body>
        <h1>WebSocket Test</h1>
        
        <div>
            <input type="text" id="token" placeholder="JWT Token" style="width: 400px;">
            <button onclick="connect()">Connect</button>
            <button onclick="disconnect()">Disconnect</button>
        </div>
        
        <div>
            <input type="text" id="conversationId" placeholder="Conversation ID">
            <button onclick="joinConversation()">Join Conversation</button>
        </div>
        
        <div>
            <input type="text" id="messageInput" placeholder="Type a message..." style="width: 300px;">
            <button onclick="sendMessage()">Send Message</button>
        </div>
        
        <div>
            <button onclick="startTyping()">Start Typing</button>
            <button onclick="stopTyping()">Stop Typing</button>
            <button onclick="getOnlineUsers()">Get Online Users</button>
        </div>
        
        <div id="messages"></div>
        
        <script>
            let ws = null;
            let currentConversationId = null;
            
            function addMessage(message, className = '') {
                const messages = document.getElementById('messages');
                const div = document.createElement('div');
                div.className = 'message ' + className;
                div.innerHTML = '<strong>' + new Date().toLocaleTimeString() + ':</strong> ' + message;
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            }
            
            function connect() {
                const token = document.getElementById('token').value;
                if (!token) {
                    addMessage('Please enter a JWT token', 'error');
                    return;
                }
                
                if (ws) {
                    ws.close();
                }
                
                ws = new WebSocket(`ws://localhost:8000/ws/chat?token=${token}`);
                
                ws.onopen = function(event) {
                    addMessage('Connected to WebSocket', 'success');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    addMessage('Received: ' + JSON.stringify(data, null, 2));
                };
                
                ws.onclose = function(event) {
                    addMessage('WebSocket connection closed', 'error');
                };
                
                ws.onerror = function(error) {
                    addMessage('WebSocket error: ' + error, 'error');
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }
            
            function joinConversation() {
                const conversationId = document.getElementById('conversationId').value;
                if (!conversationId || !ws) return;
                
                currentConversationId = conversationId;
                ws.send(JSON.stringify({
                    type: 'join_conversation',
                    conversation_id: conversationId
                }));
            }
            
            function sendMessage() {
                const message = document.getElementById('messageInput').value;
                if (!message || !ws || !currentConversationId) return;
                
                ws.send(JSON.stringify({
                    type: 'send_message',
                    conversation_id: currentConversationId,
                    content: message,
                    message_type: 'CHAT'
                }));
                
                document.getElementById('messageInput').value = '';
            }
            
            function startTyping() {
                if (!ws || !currentConversationId) return;
                
                ws.send(JSON.stringify({
                    type: 'typing',
                    conversation_id: currentConversationId,
                    is_typing: true
                }));
            }
            
            function stopTyping() {
                if (!ws || !currentConversationId) return;
                
                ws.send(JSON.stringify({
                    type: 'typing',
                    conversation_id: currentConversationId,
                    is_typing: false
                }));
            }
            
            function getOnlineUsers() {
                if (!ws) return;
                
                ws.send(JSON.stringify({
                    type: 'get_online_users'
                }));
            }
            
            // Auto-connect on Enter key
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)