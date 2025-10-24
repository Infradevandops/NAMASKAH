"""
PHASE 3: Real-time Features Implementation
Pro Tips: Connection pooling, graceful degradation, heartbeat monitoring
"""

import asyncio
import json
import logging
import time
from typing import Dict, Set, Optional, Any, List
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import redis
from dataclasses import dataclass, asdict


# Pro Tip: Connection management with health monitoring
@dataclass
class WebSocketConnection:
    websocket: WebSocket
    user_id: str
    verification_id: Optional[str]
    connected_at: datetime
    last_ping: datetime
    client_info: Dict[str, Any]


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocketConnection] = {}
        self.verification_subscribers: Dict[str, Set[str]] = {}
        self.heartbeat_interval = 30  # seconds
        self.connection_timeout = 300  # 5 minutes

    async def connect(
        self, websocket: WebSocket, user_id: str, verification_id: str = None
    ) -> str:
        """Establish WebSocket connection with proper setup"""
        await websocket.accept()

        connection_id = f"{user_id}_{int(time.time())}"

        connection = WebSocketConnection(
            websocket=websocket,
            user_id=user_id,
            verification_id=verification_id,
            connected_at=datetime.utcnow(),
            last_ping=datetime.utcnow(),
            client_info={
                "user_agent": websocket.headers.get("user-agent", ""),
                "ip": websocket.client.host if websocket.client else "unknown",
            },
        )

        self.active_connections[connection_id] = connection

        # Subscribe to verification updates
        if verification_id:
            if verification_id not in self.verification_subscribers:
                self.verification_subscribers[verification_id] = set()
            self.verification_subscribers[verification_id].add(connection_id)

        logging.info(f"WebSocket connected: {connection_id} for user {user_id}")

        # Send welcome message
        await self.send_personal_message(
            connection_id,
            {
                "type": "connection_established",
                "connection_id": connection_id,
                "server_time": datetime.utcnow().isoformat(),
            },
        )

        return connection_id

    async def disconnect(self, connection_id: str):
        """Clean disconnect with proper cleanup"""
        if connection_id in self.active_connections:
            connection = self.active_connections[connection_id]

            # Remove from verification subscribers
            if connection.verification_id:
                if connection.verification_id in self.verification_subscribers:
                    self.verification_subscribers[connection.verification_id].discard(
                        connection_id
                    )
                    if not self.verification_subscribers[connection.verification_id]:
                        del self.verification_subscribers[connection.verification_id]

            # Close WebSocket if still open
            if connection.websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await connection.websocket.close()
                except:
                    pass

            del self.active_connections[connection_id]
            logging.info(f"WebSocket disconnected: {connection_id}")

    async def send_personal_message(self, connection_id: str, message: Dict[str, Any]):
        """Send message to specific connection with error handling"""
        if connection_id not in self.active_connections:
            return False

        connection = self.active_connections[connection_id]

        try:
            if connection.websocket.client_state == WebSocketState.CONNECTED:
                await connection.websocket.send_text(json.dumps(message))
                return True
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
        except Exception as e:
            logging.error(f"Failed to send message to {connection_id}: {str(e)}")
            await self.disconnect(connection_id)

        return False

    async def broadcast_to_verification(
        self, verification_id: str, message: Dict[str, Any]
    ):
        """Broadcast message to all subscribers of a verification"""
        if verification_id not in self.verification_subscribers:
            return

        subscribers = list(self.verification_subscribers[verification_id])
        successful_sends = 0

        for connection_id in subscribers:
            if await self.send_personal_message(connection_id, message):
                successful_sends += 1

        logging.info(
            f"Broadcast to verification {verification_id}: {successful_sends}/{len(subscribers)} successful"
        )

    async def handle_heartbeat(self, connection_id: str):
        """Handle heartbeat/ping from client"""
        if connection_id in self.active_connections:
            self.active_connections[connection_id].last_ping = datetime.utcnow()

            await self.send_personal_message(
                connection_id,
                {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
            )

    async def cleanup_stale_connections(self):
        """Remove stale connections that haven't pinged recently"""
        now = datetime.utcnow()
        stale_connections = []

        for connection_id, connection in self.active_connections.items():
            if (now - connection.last_ping).total_seconds() > self.connection_timeout:
                stale_connections.append(connection_id)

        for connection_id in stale_connections:
            logging.warning(f"Removing stale connection: {connection_id}")
            await self.disconnect(connection_id)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        now = datetime.utcnow()

        return {
            "total_connections": len(self.active_connections),
            "verification_subscriptions": len(self.verification_subscribers),
            "connections_by_age": {
                "under_1min": len(
                    [
                        c
                        for c in self.active_connections.values()
                        if (now - c.connected_at).total_seconds() < 60
                    ]
                ),
                "1_to_5min": len(
                    [
                        c
                        for c in self.active_connections.values()
                        if 60 <= (now - c.connected_at).total_seconds() < 300
                    ]
                ),
                "over_5min": len(
                    [
                        c
                        for c in self.active_connections.values()
                        if (now - c.connected_at).total_seconds() >= 300
                    ]
                ),
            },
        }


# Pro Tip: Real-time SMS monitoring with fallback
class SMSMonitor:
    def __init__(self, websocket_manager: WebSocketManager, tv_client):
        self.websocket_manager = websocket_manager
        self.tv_client = tv_client
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.polling_interval = 3  # seconds
        self.max_monitoring_time = 600  # 10 minutes

    async def start_monitoring(self, verification_id: str):
        """Start monitoring SMS for a verification"""
        if verification_id in self.monitoring_tasks:
            return  # Already monitoring

        task = asyncio.create_task(self._monitor_verification(verification_id))
        self.monitoring_tasks[verification_id] = task

        logging.info(f"Started SMS monitoring for verification: {verification_id}")

    async def stop_monitoring(self, verification_id: str):
        """Stop monitoring SMS for a verification"""
        if verification_id in self.monitoring_tasks:
            self.monitoring_tasks[verification_id].cancel()
            del self.monitoring_tasks[verification_id]
            logging.info(f"Stopped SMS monitoring for verification: {verification_id}")

    async def _monitor_verification(self, verification_id: str):
        """Monitor verification for SMS messages"""
        start_time = time.time()
        last_message_count = 0

        try:
            while time.time() - start_time < self.max_monitoring_time:
                try:
                    # Check for new messages
                    messages = await self.tv_client.get_messages(verification_id)

                    if messages and len(messages) > last_message_count:
                        # New messages received
                        new_messages = messages[last_message_count:]

                        await self.websocket_manager.broadcast_to_verification(
                            verification_id,
                            {
                                "type": "sms_received",
                                "verification_id": verification_id,
                                "messages": new_messages,
                                "timestamp": datetime.utcnow().isoformat(),
                            },
                        )

                        last_message_count = len(messages)

                        # If verification is complete, stop monitoring
                        if any(msg.get("code") for msg in new_messages):
                            await self.websocket_manager.broadcast_to_verification(
                                verification_id,
                                {
                                    "type": "verification_completed",
                                    "verification_id": verification_id,
                                    "code": next(
                                        msg["code"]
                                        for msg in new_messages
                                        if msg.get("code")
                                    ),
                                    "timestamp": datetime.utcnow().isoformat(),
                                },
                            )
                            break

                    await asyncio.sleep(self.polling_interval)

                except Exception as e:
                    logging.error(
                        f"Error monitoring verification {verification_id}: {str(e)}"
                    )
                    await asyncio.sleep(self.polling_interval * 2)  # Back off on error

        except asyncio.CancelledError:
            logging.info(f"Monitoring cancelled for verification: {verification_id}")

        finally:
            # Clean up
            if verification_id in self.monitoring_tasks:
                del self.monitoring_tasks[verification_id]


# Pro Tip: Caching layer with Redis fallback
class CacheManager:
    def __init__(self, redis_url: str = None):
        self.redis_client = None
        self.local_cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes

        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logging.info("Redis cache connected")
            except Exception as e:
                logging.warning(f"Redis connection failed, using local cache: {str(e)}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                # Local cache with TTL check
                if key in self.local_cache:
                    data, timestamp = self.local_cache[key]
                    if time.time() - timestamp < self.cache_ttl:
                        return data
                    else:
                        del self.local_cache[key]
        except Exception as e:
            logging.error(f"Cache get error: {str(e)}")

        return None

    async def set(self, key: str, value: Any, ttl: int = None):
        """Set value in cache with fallback"""
        try:
            if self.redis_client:
                self.redis_client.setex(
                    key, ttl or self.cache_ttl, json.dumps(value, default=str)
                )
            else:
                # Local cache with timestamp
                self.local_cache[key] = (value, time.time())
        except Exception as e:
            logging.error(f"Cache set error: {str(e)}")

    async def delete(self, key: str):
        """Delete value from cache"""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                self.local_cache.pop(key, None)
        except Exception as e:
            logging.error(f"Cache delete error: {str(e)}")


# Pro Tip: Notification system with multiple channels
class NotificationManager:
    def __init__(
        self, websocket_manager: WebSocketManager, cache_manager: CacheManager
    ):
        self.websocket_manager = websocket_manager
        self.cache_manager = cache_manager
        self.notification_queue: List[Dict[str, Any]] = []

    async def send_notification(self, user_id: str, notification: Dict[str, Any]):
        """Send notification through available channels"""
        notification_id = f"notif_{int(time.time())}_{user_id}"

        # Add metadata
        notification.update(
            {
                "id": notification_id,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
            }
        )

        # Try WebSocket first
        user_connections = [
            conn_id
            for conn_id, conn in self.websocket_manager.active_connections.items()
            if conn.user_id == user_id
        ]

        websocket_sent = False
        for conn_id in user_connections:
            if await self.websocket_manager.send_personal_message(
                conn_id, {"type": "notification", **notification}
            ):
                websocket_sent = True

        # If WebSocket failed, queue for polling
        if not websocket_sent:
            await self.cache_manager.set(
                f"notifications:{user_id}", notification, ttl=3600
            )
            self.notification_queue.append(notification)

        logging.info(f"Notification sent to user {user_id}: {notification['type']}")

    async def get_pending_notifications(self, user_id: str) -> List[Dict[str, Any]]:
        """Get pending notifications for polling fallback"""
        notifications = await self.cache_manager.get(f"notifications:{user_id}")
        if notifications:
            await self.cache_manager.delete(f"notifications:{user_id}")
            return [notifications] if isinstance(notifications, dict) else notifications
        return []


# Initialize managers
websocket_manager = WebSocketManager()
cache_manager = CacheManager()
notification_manager = NotificationManager(websocket_manager, cache_manager)


# Pro Tip: Background task for connection cleanup
async def connection_cleanup_task():
    """Background task to clean up stale connections"""
    while True:
        try:
            await websocket_manager.cleanup_stale_connections()
            await asyncio.sleep(60)  # Run every minute
        except Exception as e:
            logging.error(f"Connection cleanup error: {str(e)}")
            await asyncio.sleep(60)
