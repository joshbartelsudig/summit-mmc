from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json
import uuid
import asyncio
from typing import List, Dict, Any, Optional
import time

from app.services.redis_service import redis_service
from app.models.schemas import ChatRequest, ChatResponse, ChatChoice, Message
from app.services.model_router import model_router
from app.services.chat_service import ChatService
from app.services.formatter_service import FormatterService
from app.utils.constants import (
    DEFAULT_MARKDOWN_SYSTEM_PROMPT,
    MODEL_GPT,
    MODEL_CLAUDE,
    MODEL_TITAN,
    MODEL_COHERE,
    MODEL_LLAMA,
    MODEL_MISTRAL,
    DEFAULT_MAX_TOKENS
)
from app.utils.chat_formatters import (
    prepare_messages_with_system_prompt,
    format_messages_for_claude,
    format_messages_for_titan,
    format_messages_for_cohere,
    format_messages_for_llama
)

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Non-streaming chat endpoint

    Args:
        request (ChatRequest): Chat request

    Returns:
        ChatResponse: Chat response
    """
    try:
        if request.stream:
            raise HTTPException(status_code=400, detail="Use /chat/stream for streaming responses")

        # Check Redis connection
        if not redis_service.is_connected():
            raise HTTPException(status_code=503, detail="Redis service unavailable")

        session_id = request.session_id or str(uuid.uuid4())
        session = None
        existing_messages = []
        messages_for_request = request.messages

        # Only interact with sessions if store_in_session is True
        if request.store_in_session:
            session = redis_service.get_session(session_id)

            if not session:
                # Create new session if it doesn't exist
                print("Creating new chat session")
                title = request.messages[0].content[:50] + "..." if request.messages else "New Chat"
                created_id = redis_service.create_session(
                    session_id=session_id,
                    title=title,
                    model_id=request.model
                )
                if not created_id:
                    raise HTTPException(status_code=500, detail="Failed to create chat session")
                session = redis_service.get_session(created_id)
                if not session:
                    raise HTTPException(status_code=500, detail="Failed to retrieve created session")
            
            # Get existing messages from the session
            existing_messages = redis_service.get_messages(session_id)
            
            # Add user's new message to the session
            for message in request.messages:
                # Only add messages that aren't already in the session
                if not any(existing_msg.content == message.content and 
                        existing_msg.role == message.role for existing_msg in existing_messages):
                    redis_service.add_message(session_id, message)
            
            # Use all messages from session for request
            messages_for_request = redis_service.get_messages(session_id)

        # Create chat request with appropriate messages
        chat_request = ChatRequest(
            messages=messages_for_request,
            model=request.model,
            stream=request.stream,
            system_prompt=request.system_prompt,
            session_id=session_id if request.store_in_session else None,
            store_in_session=request.store_in_session,
            inference_profile_arn=request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
        )

        # Generate chat completion using the chat service
        response = await ChatService.generate_chat_completion(chat_request)
        
        # Add assistant's response to the session if store_in_session is True
        if request.store_in_session:
            assistant_message = response.choices[0].message
            redis_service.add_message(session_id, assistant_message)
            
            # Get updated session data
            session_data = redis_service.get_session_data(session_id, include_messages=True)
            
            # Update response with session data
            response.session_id = session_id
            response.session = session_data

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating chat completion: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint

    Args:
        request (ChatRequest): Chat request

    Returns:
        EventSourceResponse: Streaming response
    """
    # Check if the stream flag is set
    if not request.stream:
        raise HTTPException(status_code=400, detail="Use /chat for non-streaming responses")
    
    # Check Redis connection
    if not redis_service.is_connected():
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    
    session_id = request.session_id or str(uuid.uuid4())
    session = None
    existing_messages = []
    messages_for_request = request.messages

    # Only interact with sessions if store_in_session is True
    if request.store_in_session:
        session = redis_service.get_session(session_id)

        if not session:
            # Create new session if it doesn't exist
            print("Creating new chat session")
            title = request.messages[0].content[:50] + "..." if request.messages else "New Chat"
            created_id = redis_service.create_session(
                session_id=session_id,
                title=title,
                model_id=request.model
            )
            if not created_id:
                raise HTTPException(status_code=500, detail="Failed to create chat session")
            session = redis_service.get_session(created_id)
            if not session:
                raise HTTPException(status_code=500, detail="Failed to retrieve created session")
        
        # Get existing messages from the session
        existing_messages = redis_service.get_messages(session_id)
        
        # Add user's new message to the session
        for message in request.messages:
            # Only add messages that aren't already in the session
            if not any(existing_msg.content == message.content and 
                      existing_msg.role == message.role for existing_msg in existing_messages):
                redis_service.add_message(session_id, message)

        # Use all messages from session for request
        messages_for_request = redis_service.get_messages(session_id)

    async def generate():
        try:
            messages = list(messages_for_request)
            system_content = None

            # Use custom system prompt if provided, otherwise use default
            system_prompt = request.system_prompt if request.system_prompt else DEFAULT_MARKDOWN_SYSTEM_PROMPT

            print("Streaming endpoint - System prompt:", system_prompt)  # Debug log

            # Get model type
            model_type = FormatterService.get_model_type(request.model)
            
            # Create a message to store the assistant's response
            assistant_message = Message(role="assistant", content="")
            full_content = ""

            if model_type == MODEL_GPT:
                # Add system message if not already present
                if not any(msg.role == "system" for msg in messages):
                    messages.insert(0, Message(role="system", content=system_prompt))
                    print("Added system message:", messages[0])  # Debug log

                # Azure OpenAI streaming
                print("Final messages before API call:", messages)  # Debug log
                response = model_router.azure_client.client.chat.completions.create(
                    **ChatService.prepare_azure_request(messages, request.model)
                )

                try:
                    for chunk in response:
                        print("Raw chunk:", chunk)  # Debug log
                        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                            content = chunk.choices[0].delta.content
                            full_content += content
                            print("Content:", content)  # Debug log
                            yield await FormatterService.format_streaming_chunk(content)

                    # Add the complete assistant message to the session
                    if request.store_in_session:
                        assistant_message.content = full_content
                        redis_service.add_message(session_id, assistant_message)
                        
                    # Send done event
                    yield await FormatterService.format_done_event()
                except Exception as e:
                    yield await FormatterService.format_error_event(e)

            elif model_type == MODEL_CLAUDE:
                # Format messages for Claude
                messages = []
                system_message = system_prompt

                for msg in messages_for_request:
                    if msg.role == "system":
                        system_message = msg.content + "\n\n" + system_prompt
                    else:
                        messages.append(msg)

                # Format request body
                request_body = ChatService.prepare_claude_request(
                    messages,
                    system_message,
                    request.max_tokens if hasattr(request, 'max_tokens') else DEFAULT_MAX_TOKENS,
                    request.temperature if hasattr(request, 'temperature') else 0.7
                )

                # Get Claude response stream
                client = model_router.bedrock_client
                try:
                    async for chunk in client._stream_claude_response(
                        request.model,
                        request_body,
                        client._get_model_with_profile(
                            request.model,
                            request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
                        )
                    ):
                        print("Raw chunk:", chunk)  # Debug log
                        if chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                            content = chunk["choices"][0]["delta"]["content"]
                            full_content += content
                            print("Content:", content)  # Debug log
                            yield await FormatterService.format_streaming_chunk(content)

                    # Add the complete assistant message to the session
                    if request.store_in_session:
                        assistant_message.content = full_content
                        redis_service.add_message(session_id, assistant_message)
                        
                    # Send done event
                    yield await FormatterService.format_done_event()
                except Exception as e:
                    yield await FormatterService.format_error_event(e)

            elif model_type == MODEL_TITAN:
                # Titan streaming with textGenerationConfig
                client = model_router.bedrock_client

                try:
                    async for chunk in client.generate_chat_completion_stream(
                        messages=messages_for_request,
                        model=request.model,
                        system=request.system_prompt,
                        max_tokens=request.max_tokens if hasattr(request, 'max_tokens') else DEFAULT_MAX_TOKENS,
                        inference_profile_arn=request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
                    ):
                        print("Raw chunk:", chunk)  # Debug log
                        if chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                            content = chunk["choices"][0]["delta"]["content"]
                            full_content += content
                            print("Content:", content)  # Debug log
                            yield await FormatterService.format_streaming_chunk(content)

                    # Add the complete assistant message to the session
                    if request.store_in_session:
                        assistant_message.content = full_content
                        redis_service.add_message(session_id, assistant_message)
                        
                    # Send done event
                    yield await FormatterService.format_done_event()
                except Exception as e:
                    yield await FormatterService.format_error_event(e)

            elif model_type == MODEL_COHERE:
                # Cohere streaming
                client = model_router.bedrock_client

                try:
                    async for chunk in client.generate_chat_completion_stream(
                        messages=messages_for_request,
                        model=request.model,
                        system=request.system_prompt,
                        max_tokens=request.max_tokens if hasattr(request, 'max_tokens') else DEFAULT_MAX_TOKENS,
                        inference_profile_arn=request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
                    ):
                        print("Raw chunk:", chunk)  # Debug log
                        if chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                            content = chunk["choices"][0]["delta"]["content"]
                            full_content += content
                            print("Content:", content)  # Debug log
                            yield await FormatterService.format_streaming_chunk(content)

                    # Add the complete assistant message to the session
                    if request.store_in_session:
                        assistant_message.content = full_content
                        redis_service.add_message(session_id, assistant_message)
                        
                    # Send done event
                    yield await FormatterService.format_done_event()
                except Exception as e:
                    yield await FormatterService.format_error_event(e)

            elif model_type == MODEL_LLAMA:
                # Llama streaming
                client = model_router.bedrock_client

                try:
                    async for chunk in client.generate_chat_completion_stream(
                        messages=messages_for_request,
                        model=request.model,
                        system=request.system_prompt,
                        max_tokens=request.max_tokens if hasattr(request, 'max_tokens') else DEFAULT_MAX_TOKENS,
                        inference_profile_arn=request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
                    ):
                        print("Raw chunk:", chunk)  # Debug log
                        if chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                            content = chunk["choices"][0]["delta"]["content"]
                            full_content += content
                            print("Content:", content)  # Debug log
                            yield await FormatterService.format_streaming_chunk(content)

                    # Add the complete assistant message to the session
                    if request.store_in_session:
                        assistant_message.content = full_content
                        redis_service.add_message(session_id, assistant_message)
                        
                    # Send done event
                    yield await FormatterService.format_done_event()
                except Exception as e:
                    yield await FormatterService.format_error_event(e)

            elif model_type == MODEL_MISTRAL:
                # Mistral streaming
                client = model_router.bedrock_client

                try:
                    async for chunk in client.generate_chat_completion_stream(
                        messages=messages_for_request,
                        model=request.model,
                        system=request.system_prompt,
                        max_tokens=request.max_tokens if hasattr(request, 'max_tokens') else DEFAULT_MAX_TOKENS,
                        inference_profile_arn=request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
                    ):
                        print("Raw chunk:", chunk)  # Debug log
                        if chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                            content = chunk["choices"][0]["delta"]["content"]
                            full_content += content
                            print("Content:", content)  # Debug log
                            yield await FormatterService.format_streaming_chunk(content)

                    # Add the complete assistant message to the session
                    if request.store_in_session:
                        assistant_message.content = full_content
                        redis_service.add_message(session_id, assistant_message)
                        
                    # Send done event
                    yield await FormatterService.format_done_event()
                except Exception as e:
                    yield await FormatterService.format_error_event(e)

            else:
                # Unknown model type
                error_message = f"Unsupported model type for streaming: {model_type}"
                print(error_message)
                yield await FormatterService.format_error_event(Exception(error_message))

        except Exception as e:
            print(f"Error in generate function: {str(e)}")
            yield await FormatterService.format_error_event(e)

    return EventSourceResponse(generate())
