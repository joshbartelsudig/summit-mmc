from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Message(BaseModel):
    """Chat message model"""
    role: str
    content: str
    id: Optional[str] = None
    timestamp: Optional[datetime] = None
    model: Optional[str] = None

# Alias Message as ChatMessage for consistency with other services
ChatMessage = Message

class ChatRequest(BaseModel):
    """Chat request model"""
    messages: List[Message]
    model: str
    stream: bool = False
    inference_profile_arn: Optional[str] = None
    system_prompt: Optional[str] = None  # New field for custom system prompt
    session_id: Optional[str] = None  # Session ID for chat history
    # max_tokens: Optional[int] = None
    # temperature: Optional[float] = None
    # top_p: Optional[float] = None
    # top_k: Optional[int] = None
    # ignore_history: Optional[bool] = False  # Flag to ignore chat history

class ChatChoice(BaseModel):
    """Chat choice model for response"""
    message: Message
    finish_reason: str

class ChatResponse(BaseModel):
    """Chat response model"""
    id: str
    model: str
    choices: List[ChatChoice]
    session_id: Optional[str] = None  # Session ID for chat history

class Model(BaseModel):
    """Model information"""
    id: str
    provider: str
    name: str

class ModelInfo(BaseModel):
    """Detailed model information"""
    id: str
    provider: str
    name: str

class ModelsResponse(BaseModel):
    """Response model for listing available models"""
    models: List[Model]

class ChatSession(BaseModel):
    """Chat session model"""
    id: str
    title: str
    date: datetime
    preview: str = ""
    message_count: int = 0
    model_id: Optional[str] = None
    last_updated: Optional[datetime] = None
    messages: Optional[List[Message]] = None

class ChatSessionResponse(BaseModel):
    """Response model for chat session operations"""
    session: ChatSession

class ChatSessionsResponse(BaseModel):
    """Response model for listing chat sessions"""
    sessions: List[ChatSession]
