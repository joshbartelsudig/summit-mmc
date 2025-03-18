from fastapi import APIRouter, HTTPException, Body, Query, Path, Depends
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from app.models.schemas import (
    ChatSession, 
    ChatSessionResponse, 
    ChatSessionsResponse,
    Message
)
from app.services.redis_service import redis_service

router = APIRouter()

@router.get("/sessions", response_model=ChatSessionsResponse)
async def list_sessions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List chat sessions
    
    Args:
        limit: Maximum number of sessions to return
        offset: Offset for pagination
        
    Returns:
        ChatSessionsResponse: List of chat sessions
    """
    try:
        # Check Redis connection
        if not redis_service.is_connected():
            raise HTTPException(status_code=503, detail="Redis service unavailable")
        
        # Get sessions from Redis
        sessions = redis_service.list_sessions(limit=limit, offset=offset)
        
        return ChatSessionsResponse(sessions=sessions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    title: str = Body("New Chat", embed=True),
    model_id: Optional[str] = Body(None, embed=True)
):
    """
    Create a new chat session
    
    Args:
        title: Session title
        model_id: Model ID to use for this session
        
    Returns:
        ChatSessionResponse: Created session
    """
    try:
        # Check Redis connection
        if not redis_service.is_connected():
            raise HTTPException(status_code=503, detail="Redis service unavailable")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create session in Redis
        created_id = redis_service.create_session(
            session_id=session_id, 
            title=title,
            model_id=model_id or ""
        )
        
        if not created_id:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        # Get session data
        session = redis_service.get_session_data(created_id)
        if not session:
            raise HTTPException(status_code=500, detail="Failed to retrieve created session")
        
        return ChatSessionResponse(session=session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: str = Path(..., description="Session ID"),
    include_messages: bool = Query(False, description="Include messages in response")
):
    """
    Get a chat session by ID
    
    Args:
        session_id: Session ID
        include_messages: Whether to include messages in the response
        
    Returns:
        ChatSessionResponse: Session data
    """
    try:
        # Check Redis connection
        if not redis_service.is_connected():
            raise HTTPException(status_code=503, detail="Redis service unavailable")
        
        # Get session from Redis
        session = redis_service.get_session_data(
            session_id=session_id,
            include_messages=include_messages
        )
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return ChatSessionResponse(session=session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session: {str(e)}")

@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: str = Path(..., description="Session ID"),
    title: Optional[str] = Body(None, embed=True),
    model_id: Optional[str] = Body(None, embed=True)
):
    """
    Update a chat session
    
    Args:
        session_id: Session ID
        title: New session title
        model_id: New model ID
        
    Returns:
        ChatSessionResponse: Updated session
    """
    try:
        # Check Redis connection
        if not redis_service.is_connected():
            raise HTTPException(status_code=503, detail="Redis service unavailable")
        
        # Check if session exists
        session = redis_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Update session in Redis
        success = redis_service.update_session(
            session_id=session_id,
            title=title,
            model_id=model_id
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update session")
        
        # Get updated session
        updated_session = redis_service.get_session_data(session_id)
        
        return ChatSessionResponse(session=updated_session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating session: {str(e)}")

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str = Path(..., description="Session ID")
):
    """
    Delete a chat session
    
    Args:
        session_id: Session ID
        
    Returns:
        dict: Success message
    """
    try:
        # Check Redis connection
        if not redis_service.is_connected():
            raise HTTPException(status_code=503, detail="Redis service unavailable")
        
        # Check if session exists
        session = redis_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Delete session in Redis
        success = redis_service.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete session")
        
        return {"message": f"Session {session_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str = Path(..., description="Session ID"),
    limit: Optional[int] = Query(None, description="Maximum number of messages to return")
):
    """
    Get messages for a chat session
    
    Args:
        session_id: Session ID
        limit: Maximum number of messages to return
        
    Returns:
        dict: List of messages
    """
    try:
        # Check Redis connection
        if not redis_service.is_connected():
            raise HTTPException(status_code=503, detail="Redis service unavailable")
        
        # Check if session exists
        session = redis_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Get messages from Redis
        messages = redis_service.get_messages(session_id, limit=limit)
        
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting messages: {str(e)}")

@router.post("/sessions/{session_id}/messages")
async def add_session_message(
    session_id: str = Path(..., description="Session ID"),
    message: Message = Body(..., description="Message to add")
):
    """
    Add a message to a chat session
    
    Args:
        session_id: Session ID
        message: Message to add
        
    Returns:
        dict: Success message
    """
    try:
        # Check Redis connection
        if not redis_service.is_connected():
            raise HTTPException(status_code=503, detail="Redis service unavailable")
        
        # Check if session exists
        session = redis_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Add message to Redis
        success = redis_service.add_message(session_id, message)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add message")
        
        return {"message": "Message added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding message: {str(e)}")

@router.delete("/sessions/{session_id}/messages")
async def clear_session_messages(
    session_id: str = Path(..., description="Session ID")
):
    """
    Clear all messages for a chat session
    
    Args:
        session_id: Session ID
        
    Returns:
        dict: Success message
    """
    try:
        # Check Redis connection
        if not redis_service.is_connected():
            raise HTTPException(status_code=503, detail="Redis service unavailable")
        
        # Check if session exists
        session = redis_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Clear messages in Redis
        success = redis_service.clear_messages(session_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear messages")
        
        return {"message": f"Messages for session {session_id} cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing messages: {str(e)}")
