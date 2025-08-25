"""WebSocket manager for real-time updates."""

import json
import uuid
from typing import Dict, List, Set

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from .database.connection import get_database
from .models.user import User


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Store active connections by user ID
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_info: Dict[WebSocket, Dict[str, any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str) -> bool:
        """Accept WebSocket connection and store user mapping.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
            
        Returns:
            True if connection successful
        """
        try:
            await websocket.accept()
            
            # Add to active connections
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            
            self.active_connections[user_id].add(websocket)
            
            # Store connection metadata
            self.connection_info[websocket] = {
                "user_id": user_id,
                "connected_at": str(uuid.uuid4()),  # Simple connection ID
                "subscriptions": set()  # Task/project subscriptions
            }
            
            # Send welcome message
            await self.send_personal_message({
                "type": "connection_established",
                "message": "WebSocket connection established",
                "connection_id": self.connection_info[websocket]["connected_at"]
            }, user_id)
            
            return True
            
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            return False
    
    def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
        """
        if websocket in self.connection_info:
            user_id = self.connection_info[websocket]["user_id"]
            
            # Remove from user's connections
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                
                # Clean up empty connection sets
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove connection info
            del self.connection_info[websocket]
    
    async def send_personal_message(self, message: Dict[str, any], user_id: str) -> None:
        """Send message to all connections for a specific user.
        
        Args:
            message: Message dictionary to send
            user_id: Target user ID
        """
        if user_id not in self.active_connections:
            return
        
        message_str = json.dumps(message, default=str)
        dead_connections = []
        
        for connection in self.active_connections[user_id].copy():
            try:
                await connection.send_text(message_str)
            except Exception:
                # Connection is dead, mark for removal
                dead_connections.append(connection)
        
        # Clean up dead connections
        for connection in dead_connections:
            self.disconnect(connection)
    
    async def broadcast_to_subscribed(
        self, 
        message: Dict[str, any], 
        subscription_key: str
    ) -> None:
        """Broadcast message to all users subscribed to a specific key.
        
        Args:
            message: Message to broadcast
            subscription_key: Subscription key (e.g., task_id, project_id)
        """
        message_str = json.dumps(message, default=str)
        dead_connections = []
        
        for websocket, info in self.connection_info.items():
            if subscription_key in info.get("subscriptions", set()):
                try:
                    await websocket.send_text(message_str)
                except Exception:
                    dead_connections.append(websocket)
        
        # Clean up dead connections
        for connection in dead_connections:
            self.disconnect(connection)
    
    async def subscribe_to_updates(
        self, 
        websocket: WebSocket, 
        subscription_key: str
    ) -> None:
        """Subscribe connection to specific updates.
        
        Args:
            websocket: WebSocket connection
            subscription_key: Key to subscribe to
        """
        if websocket in self.connection_info:
            self.connection_info[websocket]["subscriptions"].add(subscription_key)
    
    async def unsubscribe_from_updates(
        self, 
        websocket: WebSocket, 
        subscription_key: str
    ) -> None:
        """Unsubscribe connection from specific updates.
        
        Args:
            websocket: WebSocket connection
            subscription_key: Key to unsubscribe from
        """
        if websocket in self.connection_info:
            self.connection_info[websocket]["subscriptions"].discard(subscription_key)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get connection count for specific user."""
        return len(self.active_connections.get(user_id, set()))
    
    async def send_task_update(
        self, 
        task_id: str, 
        update_type: str, 
        data: Dict[str, any],
        user_id: str
    ) -> None:
        """Send task-specific update.
        
        Args:
            task_id: Task ID
            update_type: Type of update
            data: Update data
            user_id: Target user ID
        """
        message = {
            "type": "task_update",
            "task_id": task_id,
            "update_type": update_type,
            "data": data,
            "timestamp": str(uuid.uuid4())  # Simple timestamp
        }
        
        await self.send_personal_message(message, user_id)
        # Also notify subscribers
        await self.broadcast_to_subscribed(message, f"task_{task_id}")
    
    async def send_build_update(
        self, 
        build_id: str, 
        task_id: str,
        status: str, 
        data: Dict[str, any],
        user_id: str
    ) -> None:
        """Send build status update.
        
        Args:
            build_id: Build ID
            task_id: Related task ID
            status: Build status
            data: Additional data
            user_id: Target user ID
        """
        message = {
            "type": "build_update",
            "build_id": build_id,
            "task_id": task_id,
            "status": status,
            "data": data,
            "timestamp": str(uuid.uuid4())
        }
        
        await self.send_personal_message(message, user_id)
        await self.broadcast_to_subscribed(message, f"task_{task_id}")
    
    async def send_progress_update(
        self,
        task_id: str,
        progress_data: Dict[str, any],
        user_id: str
    ) -> None:
        """Send binary search progress update.
        
        Args:
            task_id: Task ID
            progress_data: Progress information
            user_id: Target user ID
        """
        message = {
            "type": "progress_update",
            "task_id": task_id,
            "progress": progress_data,
            "timestamp": str(uuid.uuid4())
        }
        
        await self.send_personal_message(message, user_id)
        await self.broadcast_to_subscribed(message, f"task_{task_id}")


# Global connection manager instance
manager = ConnectionManager()


async def verify_websocket_token(token: str) -> tuple[bool, str | None]:
    """Verify WebSocket authentication token.
    
    Args:
        token: JWT token
        
    Returns:
        Tuple of (is_valid, user_id)
    """
    try:
        from .auth.security import verify_token
        from .database.connection import get_database
        
        # Verify token
        token_data = verify_token(token, token_type="access")
        if not token_data:
            return False, None
        
        # Verify user exists and is active
        db = next(get_database())
        user = db.query(User).filter(User.username == token_data.username).first()
        
        if not user or not user.is_active:
            return False, None
        
        return True, str(user.id)
        
    except Exception as e:
        print(f"WebSocket token verification error: {e}")
        return False, None


async def handle_websocket_message(
    websocket: WebSocket, 
    message_data: Dict[str, any]
) -> None:
    """Handle incoming WebSocket message.
    
    Args:
        websocket: WebSocket connection
        message_data: Parsed message data
    """
    message_type = message_data.get("type")
    
    if message_type == "subscribe":
        # Subscribe to updates for specific resource
        subscription_key = message_data.get("key")
        if subscription_key:
            await manager.subscribe_to_updates(websocket, subscription_key)
            
            # Send confirmation
            await websocket.send_text(json.dumps({
                "type": "subscription_confirmed",
                "key": subscription_key
            }))
    
    elif message_type == "unsubscribe":
        # Unsubscribe from updates
        subscription_key = message_data.get("key")
        if subscription_key:
            await manager.unsubscribe_from_updates(websocket, subscription_key)
            
            await websocket.send_text(json.dumps({
                "type": "unsubscription_confirmed", 
                "key": subscription_key
            }))
    
    elif message_type == "ping":
        # Handle ping/pong for connection keepalive
        await websocket.send_text(json.dumps({
            "type": "pong",
            "timestamp": message_data.get("timestamp")
        }))
    
    else:
        # Unknown message type
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }))