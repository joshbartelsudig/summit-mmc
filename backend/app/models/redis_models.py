from datetime import datetime
from typing import List, Optional
from redis_om import HashModel, Field, Migrator, get_redis_connection
import json
import os
import logging

from app.models.schemas import Message

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Redis OM connection
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_password = os.getenv("REDIS_PASSWORD", "")
redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"

try:
    redis_connection = get_redis_connection(url=redis_url)
    logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")
    redis_connection = None

class RedisChatSession(HashModel):
    """Redis model for chat sessions"""
    title: str = Field(index=True)
    date: datetime = Field(index=True)
    preview: str = Field(index=True, default="")
    message_count: int = Field(index=True, default=0)
    user_id: Optional[str] = Field(index=True, default=None)
    model_id: str = Field(index=True)
    last_updated: datetime = Field(index=True)

    class Meta:
        global_key_prefix = "mmc"
        model_key_prefix = "chat_session"
        database = redis_connection

    @property
    def redis(self):
        """Get the Redis client"""
        return redis_connection

    def add_message(self, message: Message) -> None:
        """Add a message to the session"""
        # Store message in a separate Redis list
        message_key = f"mmc:chat_session:{self.pk}:messages"
        
        # Add timestamp if not present
        if not message.timestamp:
            message_dict = message.model_dump()
            message_dict["timestamp"] = datetime.utcnow().isoformat()
        else:
            message_dict = message.model_dump()
            
        # Add message ID if not present
        if not message_dict.get("id"):
            import uuid
            message_dict["id"] = str(uuid.uuid4())
            
        self.redis.rpush(message_key, json.dumps(message_dict))
        self.message_count += 1
        self.last_updated = datetime.utcnow()
        
        if message.role == "assistant":
            # Update preview with the first few words of the latest assistant message
            preview_words = message.content.split()[:10]
            self.preview = " ".join(preview_words) + ("..." if len(preview_words) == 10 else "")
        self.save()

    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """Get messages from the session"""
        message_key = f"mmc:chat_session:{self.pk}:messages"
        # Get all messages or the last N messages if limit is specified
        if limit:
            messages_json = self.redis.lrange(message_key, -limit, -1)
        else:
            messages_json = self.redis.lrange(message_key, 0, -1)
        
        # Convert JSON strings back to Message objects
        messages = []
        for msg_json in messages_json:
            try:
                msg_dict = json.loads(msg_json)
                # Convert timestamp string to datetime if present
                if "timestamp" in msg_dict and msg_dict["timestamp"]:
                    try:
                        msg_dict["timestamp"] = datetime.fromisoformat(msg_dict["timestamp"])
                    except (ValueError, TypeError):
                        msg_dict["timestamp"] = None
                messages.append(Message(**msg_dict))
            except Exception as e:
                logger.error(f"Error parsing message JSON: {str(e)}")
        
        return messages

    def clear_messages(self) -> None:
        """Clear all messages for this session"""
        message_key = f"mmc:chat_session:{self.pk}:messages"
        self.redis.delete(message_key)
        self.message_count = 0
        self.preview = ""
        self.save()

    @classmethod
    def delete(cls, pk: str) -> None:
        """Delete a session by its primary key"""
        try:
            session = cls.get(pk)
            if session:
                session.clear_messages()  # Clear messages first
                super().delete(pk)  # Call parent class's delete method
        except Exception as e:
            logger.error(f"Error deleting session {pk}: {str(e)}")

# Run migrations if Redis is connected
if redis_connection:
    try:
        Migrator().run()
        logger.info("Redis OM migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running Redis OM migrations: {str(e)}")
