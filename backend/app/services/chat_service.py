"""
Service for handling chat operations.
"""

import uuid
from typing import List, Dict, Any, Optional, Union

from app.models.schemas import (
    Message, 
    ChatRequest, 
    ChatResponse, 
    ChatChoice
)
from app.services.model_router import model_router
from app.utils.constants import (
    DEFAULT_MAX_TOKENS,
    MODEL_CLAUDE
)
from app.utils.chat_formatters import (
    prepare_messages_with_system_prompt,
    format_messages_for_claude,
    format_messages_for_titan,
    format_messages_for_cohere,
    format_messages_for_llama
)


class ChatService:
    """Service for handling chat operations."""
    
    @staticmethod
    async def generate_chat_completion(request: ChatRequest) -> ChatResponse:
        """
        Generate a chat completion.
        
        Args:
            request (ChatRequest): The chat request
            
        Returns:
            ChatResponse: The chat response
        """
        # Handle messages based on model type
        messages, system_content = prepare_messages_with_system_prompt(
            request.messages,
            request.system_prompt,
            request.model
        )
        
        # Route the request to the appropriate provider
        response = await model_router.route_chat_completion(
            messages=messages,
            model=request.model,
            system=system_content if request.model.startswith(MODEL_CLAUDE) else None,
            max_tokens=DEFAULT_MAX_TOKENS if request.model.startswith(MODEL_CLAUDE) else None,
            inference_profile_arn=request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
        )
        
        # Format the response
        return ChatResponse(
            id=str(uuid.uuid4()),
            model=request.model,
            choices=[
                ChatChoice(
                    message=Message(
                        role="assistant",
                        content=response["choices"][0]["message"]["content"]
                    ),
                    finish_reason=response["choices"][0].get("finish_reason", "stop")
                )
            ]
        )
    
    @staticmethod
    def prepare_azure_request(messages: List[Message], model: str) -> Dict[str, Any]:
        """
        Prepare a request for Azure OpenAI.
        
        Args:
            messages (List[Message]): The messages
            model (str): The model name
            
        Returns:
            Dict[str, Any]: The request parameters
        """
        return {
            "model": model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "stream": True,
            "max_tokens": DEFAULT_MAX_TOKENS
        }
    
    @staticmethod
    def prepare_claude_request(
        messages: List[Message], 
        system_message: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Prepare a request for Claude.
        
        Args:
            messages (List[Message]): The messages
            system_message (str): The system message
            max_tokens (int): Maximum tokens
            temperature (float): Temperature
            
        Returns:
            Dict[str, Any]: The request body
        """
        formatted_messages, system = format_messages_for_claude(messages, system_message)
        
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": formatted_messages
        }
    
    @staticmethod
    def prepare_titan_request(messages: List[Message]) -> str:
        """
        Prepare a request for Titan.
        
        Args:
            messages (List[Message]): The messages
            
        Returns:
            str: The formatted input text
        """
        return format_messages_for_titan(messages)
    
    @staticmethod
    def prepare_cohere_request(messages: List[Message]) -> List[Dict[str, str]]:
        """
        Prepare a request for Cohere.
        
        Args:
            messages (List[Message]): The messages
            
        Returns:
            List[Dict[str, str]]: The formatted messages
        """
        return format_messages_for_cohere(messages)
    
    @staticmethod
    def prepare_llama_request(messages: List[Message]) -> str:
        """
        Prepare a request for Llama.
        
        Args:
            messages (List[Message]): The messages
            
        Returns:
            str: The formatted prompt
        """
        return format_messages_for_llama(messages)
