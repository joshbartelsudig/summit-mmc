"""
Service for formatting chat messages and responses.
"""

import json
import uuid
from typing import Dict, Any, List, Optional, AsyncGenerator

from app.models.schemas import Message, ChatRequest
from app.utils.constants import (
    STREAM_RETRY_TIMEOUT,
    EVENT_MESSAGE,
    EVENT_DONE,
    EVENT_ERROR,
    DONE_MARKER,
    MODEL_GPT,
    MODEL_CLAUDE,
    MODEL_TITAN,
    MODEL_COHERE,
    MODEL_LLAMA,
    MODEL_MISTRAL
)
from app.utils.chat_formatters import format_code_blocks


class FormatterService:
    """Service for formatting chat messages and responses."""

    @staticmethod
    async def format_streaming_chunk(
        content: str,
        event_type: str = EVENT_MESSAGE,
        format_code: bool = True
    ) -> Dict[str, Any]:
        """
        Format a streaming chunk.

        Args:
            content (str): The content to stream
            event_type (str): The event type
            format_code (bool): Whether to format code blocks

        Returns:
            Dict[str, Any]: Formatted event data
        """
        print(f"DEBUG: FormatterService input content: {content}")
        if format_code:
            content = format_code_blocks(content)
            print(f"DEBUG: FormatterService after code blocks: {content}")

        formatted_event = {
            "event": event_type,
            "id": str(uuid.uuid4()),
            "retry": STREAM_RETRY_TIMEOUT,
            "data": json.dumps({"content": content})
        }
        print(f"DEBUG: FormatterService output event: {formatted_event}")
        return formatted_event

    @staticmethod
    async def format_done_event() -> Dict[str, Any]:
        """
        Format a done event.

        Returns:
            Dict[str, Any]: Done event data
        """
        return {
            "event": EVENT_DONE,
            "id": str(uuid.uuid4()),
            "retry": STREAM_RETRY_TIMEOUT,
            "data": json.dumps({"content": DONE_MARKER})
        }

    @staticmethod
    async def format_error_event(error: Exception) -> Dict[str, Any]:
        """
        Format an error event.

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

    @staticmethod
    def get_model_type(model: str) -> str:
        """
        Get the model type from the model name.

        Args:
            model (str): The model name

        Returns:
            str: The model type
        """
        if model.startswith(MODEL_GPT):
            return MODEL_GPT
        elif model.startswith(MODEL_CLAUDE):
            return MODEL_CLAUDE
        elif model.startswith(MODEL_TITAN):
            return MODEL_TITAN
        elif model.startswith(MODEL_COHERE):
            return MODEL_COHERE
        elif model.startswith(MODEL_LLAMA):
            return MODEL_LLAMA
        elif model.startswith(MODEL_MISTRAL):
            return MODEL_MISTRAL
        else:
            return "unknown"

    @staticmethod
    async def create_streaming_generator(
        request: ChatRequest,
        stream_func: AsyncGenerator
    ) -> AsyncGenerator:
        """
        Create a streaming generator.

        Args:
            request (ChatRequest): The chat request
            stream_func (AsyncGenerator): The streaming function

        Returns:
            AsyncGenerator: The streaming generator
        """
        async for chunk in stream_func:
            yield chunk

        # Send done event
        yield await FormatterService.format_done_event()

    @staticmethod
    def format_messages_for_api(messages: List[Message], model_type: str) -> List[Dict[str, Any]]:
        """
        Format messages for API request.

        Args:
            messages (List[Message]): The messages
            model_type (str): The model type

        Returns:
            List[Dict[str, Any]]: Formatted messages
        """
        if model_type == MODEL_GPT:
            return [{"role": msg.role, "content": msg.content} for msg in messages]
        elif model_type == MODEL_CLAUDE:
            return [
                {
                    "role": msg.role,
                    "content": [{"type": "text", "text": msg.content}]
                }
                for msg in messages
            ]
        else:
            # Default format
            return [{"role": msg.role, "content": msg.content} for msg in messages]
