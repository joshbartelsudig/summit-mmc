from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Message(BaseModel):
    """Chat message model"""
    role: str
    content: str

# Alias Message as ChatMessage for consistency with other services
ChatMessage = Message

class ChatRequest(BaseModel):
    """Chat request model"""
    messages: List[Message]
    model: str
    stream: bool = False
    inference_profile_arn: Optional[str] = None

class ChatChoice(BaseModel):
    """Chat choice model for response"""
    message: Message
    finish_reason: str

class ChatResponse(BaseModel):
    """Chat response model"""
    id: str
    model: str
    choices: List[ChatChoice]

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
