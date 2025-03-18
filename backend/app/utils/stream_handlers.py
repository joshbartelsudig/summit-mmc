"""
Utility functions for handling streaming responses from different models.
"""

import json
import uuid
from typing import Dict, Any, AsyncGenerator, Callable, Optional

from app.utils.constants import (
    STREAM_RETRY_TIMEOUT,
    EVENT_MESSAGE,
    EVENT_DONE,
    EVENT_ERROR,
    DONE_MARKER
)
from app.utils.chat_formatters import format_code_blocks


async def handle_streaming_chunk(
    content: str,
    event_type: str = EVENT_MESSAGE,
    format_code: bool = True
) -> Dict[str, Any]:
    """
    Handle a streaming chunk and format it appropriately.
    
    Args:
        content (str): The content to stream
        event_type (str): The event type
        format_code (bool): Whether to format code blocks
        
    Returns:
        Dict[str, Any]: Formatted event data
    """
    if format_code:
        content = format_code_blocks(content)
        
    return {
        "event": event_type,
        "id": str(uuid.uuid4()),
        "retry": STREAM_RETRY_TIMEOUT,
        "data": json.dumps({"content": content})
    }


async def handle_done_event() -> Dict[str, Any]:
    """
    Create a done event.
    
    Returns:
        Dict[str, Any]: Done event data
    """
    return await handle_streaming_chunk(DONE_MARKER, EVENT_DONE, False)


async def handle_error_event(error: Exception) -> Dict[str, Any]:
    """
    Create an error event.
    
    Args:
        error (Exception): The error that occurred
        
    Returns:
        Dict[str, Any]: Error event data
    """
    return {
        "event": EVENT_ERROR,
        "id": str(uuid.uuid4()),
        "retry": STREAM_RETRY_TIMEOUT,
        "data": json.dumps({"error": f"Streaming error: {str(error)}"})
    }


async def stream_gpt_response(
    response: Any,
    yield_func: Callable[[Dict[str, Any]], None]
) -> None:
    """
    Stream a GPT response.
    
    Args:
        response: The streaming response from the API
        yield_func: Function to yield the formatted chunks
    """
    try:
        for chunk in response:
            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                yield_func(await handle_streaming_chunk(content))
                
        yield_func(await handle_done_event())
    except Exception as e:
        yield_func(await handle_error_event(e))


async def stream_claude_response(
    client: Any,
    model: str,
    request_body: Dict[str, Any],
    model_with_profile: Optional[str] = None,
    yield_func: Callable[[Dict[str, Any]], None] = None
) -> None:
    """
    Stream a Claude response.
    
    Args:
        client: The Bedrock client
        model: The model name
        request_body: The request body
        model_with_profile: The model with profile
        yield_func: Function to yield the formatted chunks
    """
    try:
        async for chunk in client._stream_claude_response(
            model, 
            request_body, 
            client._get_model_with_profile(model, model_with_profile)
        ):
            if chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                content = chunk["choices"][0]["delta"]["content"]
                yield_func(await handle_streaming_chunk(content))
                
        yield_func(await handle_done_event())
    except Exception as e:
        yield_func(await handle_error_event(e))


async def stream_titan_response(
    client: Any,
    model: str,
    input_text: str,
    model_with_profile: Optional[str] = None,
    yield_func: Callable[[Dict[str, Any]], None] = None
) -> None:
    """
    Stream a Titan response.
    
    Args:
        client: The Bedrock client
        model: The model name
        input_text: The input text
        model_with_profile: The model with profile
        yield_func: Function to yield the formatted chunks
    """
    try:
        async for chunk in client._stream_titan_response(
            model, 
            input_text, 
            client._get_model_with_profile(model, model_with_profile)
        ):
            if "outputText" in chunk:
                content = chunk["outputText"]
                yield_func(await handle_streaming_chunk(content))
                
        yield_func(await handle_done_event())
    except Exception as e:
        yield_func(await handle_error_event(e))


async def stream_cohere_response(
    client: Any,
    model: str,
    messages: Any,
    model_with_profile: Optional[str] = None,
    yield_func: Callable[[Dict[str, Any]], None] = None
) -> None:
    """
    Stream a Cohere response.
    
    Args:
        client: The Bedrock client
        model: The model name
        messages: The messages
        model_with_profile: The model with profile
        yield_func: Function to yield the formatted chunks
    """
    try:
        async for chunk in client._stream_cohere_response(
            model, 
            messages, 
            client._get_model_with_profile(model, model_with_profile)
        ):
            if "generations" in chunk and len(chunk["generations"]) > 0:
                if "text" in chunk["generations"][0]:
                    content = chunk["generations"][0]["text"]
                    yield_func(await handle_streaming_chunk(content))
                
        yield_func(await handle_done_event())
    except Exception as e:
        yield_func(await handle_error_event(e))


async def stream_llama_response(
    client: Any,
    model: str,
    prompt: str,
    model_with_profile: Optional[str] = None,
    yield_func: Callable[[Dict[str, Any]], None] = None
) -> None:
    """
    Stream a Llama response.
    
    Args:
        client: The Bedrock client
        model: The model name
        prompt: The prompt
        model_with_profile: The model with profile
        yield_func: Function to yield the formatted chunks
    """
    try:
        async for chunk in client._stream_llama_response(
            model, 
            prompt, 
            client._get_model_with_profile(model, model_with_profile)
        ):
            if "generation" in chunk:
                content = chunk["generation"]
                yield_func(await handle_streaming_chunk(content))
                
        yield_func(await handle_done_event())
    except Exception as e:
        yield_func(await handle_error_event(e))
