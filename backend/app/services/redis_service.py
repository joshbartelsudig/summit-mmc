import redis
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import uuid
from redis_om import get_redis_connection

from app.models.schemas import Message, ChatSession
from app.models.redis_models import RedisChatSession

logger = logging.getLogger(__name__)

class RedisService:
    """Redis service for chat history management"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_password = os.getenv("REDIS_PASSWORD", "")
        
        logger.info(f"Initializing Redis connection to {self.redis_host}:{self.redis_port}")
        
        # Connect to Redis using Redis OM's connection
        try:
            redis_url = f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"
            self.redis = get_redis_connection(url=redis_url)
            ping_result = self.redis.ping()
            logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}, ping result: {ping_result}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            logger.error(f"Redis connection details: host={self.redis_host}, port={self.redis_port}, password={'*****' if self.redis_password else 'not set'}")
            self.redis = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {str(e)}")
            self.redis = None

    def is_connected(self) -> bool:
        """Check if connected to Redis"""
        if not self.redis:
            logger.warning("Redis client is not initialized")
            return False
        try:
            return self.redis.ping()
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error in is_connected: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in Redis is_connected: {str(e)}")
            return False
    
    def create_session(self, session_id: Optional[str] = None, title: str = "New Chat", model_id: str = "") -> Optional[str]:
        """Create a new chat session"""
        if not self.is_connected():
            logger.error("Cannot create session: Redis not connected")
            return None
        
        try:
            # Generate a session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
                
            session = RedisChatSession(
                pk=session_id,
                title=title,
                date=datetime.utcnow(),
                model_id=model_id,
                last_updated=datetime.utcnow()
            )
            session.save()
            logger.info(f"Created new session: {session_id} with title: {title}")
            return session_id
        except Exception as e:
            logger.error(f"Error creating session {session_id}: {str(e)}")
            return None
    
    def get_session(self, session_id: str) -> Optional[RedisChatSession]:
        """Get a chat session by ID"""
        if not self.is_connected():
            logger.error(f"Cannot get session {session_id}: Redis not connected")
            return None
        
        try:
            session = RedisChatSession.get(session_id)
            if not session:
                logger.warning(f"Session not found: {session_id}")
                return None
            return session
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {str(e)}")
            return None
    
    def get_session_data(self, session_id: str, include_messages: bool = False, message_limit: Optional[int] = None) -> Optional[ChatSession]:
        """Get a chat session as a ChatSession model"""
        if not self.is_connected():
            logger.error(f"Cannot get session data {session_id}: Redis not connected")
            return None
            
        try:
            redis_session = self.get_session(session_id)
            if not redis_session:
                return None
                
            # Convert to ChatSession model
            session = ChatSession(
                id=session_id,
                title=redis_session.title,
                date=redis_session.date,
                preview=redis_session.preview,
                message_count=redis_session.message_count,
                model_id=redis_session.model_id,
                last_updated=redis_session.last_updated
            )
            
            # Include messages if requested
            if include_messages:
                session.messages = self.get_messages(session_id, limit=message_limit)
                
            return session
        except Exception as e:
            logger.error(f"Error getting session data {session_id}: {str(e)}")
            return None
    
    def update_session(self, session_id: str, title: Optional[str] = None, model_id: Optional[str] = None) -> bool:
        """Update a chat session"""
        if not self.is_connected():
            logger.error("Cannot update session: Redis not connected")
            return False
        
        try:
            session = self.get_session(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return False
            
            if title is not None:
                session.title = title
            if model_id is not None:
                session.model_id = model_id
            
            session.last_updated = datetime.utcnow()
            session.save()
            return True
        except Exception as e:
            logger.error(f"Error updating session: {str(e)}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session"""
        if not self.is_connected():
            logger.error("Cannot delete session: Redis not connected")
            return False
        
        try:
            RedisChatSession.delete(session_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            return False
    
    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[ChatSession]:
        """List chat sessions, sorted by most recent first"""
        if not self.is_connected():
            logger.error("Cannot list sessions: Redis not connected")
            return []
        
        try:
            # Use Redis OM to query sessions sorted by last_updated
            query_result = RedisChatSession.find().sort_by("-last_updated")
            
            if not query_result:
                logger.info("No sessions found in Redis")
                return []
            
            # Get paginated sessions
            sessions_data = query_result.page(offset, limit)
            
            # Convert to ChatSession objects
            sessions = []
            for session_data in sessions_data:
                sessions.append(ChatSession(
                    id=session_data.pk,
                    title=session_data.title,
                    date=session_data.date,
                    preview=session_data.preview,
                    message_count=session_data.message_count,
                    model_id=session_data.model_id,
                    last_updated=session_data.last_updated
                ))
            
            return sessions
        except Exception as e:
            logger.error(f"Error listing sessions: {str(e)}")
            return []
    
    def add_message(self, session_id: str, message: Message) -> bool:
        """Add a message to a session"""
        if not self.is_connected():
            logger.error("Cannot add message: Redis not connected")
            return False
            
        try:
            session = self.get_session(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return False
                
            session.add_message(message)
            return True
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            return False
    
    def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Message]:
        """Get messages from a session"""
        if not self.is_connected():
            logger.error("Cannot get messages: Redis not connected")
            return []
            
        try:
            session = self.get_session(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return []
                
            return session.get_messages(limit)
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            return []
    
    def clear_messages(self, session_id: str) -> bool:
        """Clear all messages for a session"""
        if not self.is_connected():
            logger.error("Cannot clear messages: Redis not connected")
            return False
            
        try:
            session = self.get_session(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return False
                
            session.clear_messages()
            return True
        except Exception as e:
            logger.error(f"Error clearing messages: {str(e)}")
            return False

# Create a global instance of RedisService
redis_service = RedisService()
