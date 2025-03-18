from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json
import uuid
import asyncio
from typing import List, Dict, Any, Optional
import time

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

        # Generate chat completion using the chat service
        return await ChatService.generate_chat_completion(request)
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

    async def generate():
        try:
            messages = list(request.messages)
            system_content = None

            # Use custom system prompt if provided, otherwise use default
            system_prompt = request.system_prompt if request.system_prompt else DEFAULT_MARKDOWN_SYSTEM_PROMPT
            
            print("Streaming endpoint - System prompt:", system_prompt)  # Debug log

            # Get model type
            model_type = FormatterService.get_model_type(request.model)

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
                            print("Content:", content)  # Debug log
                            yield await FormatterService.format_streaming_chunk(content)

                    # Send done event
                    yield await FormatterService.format_done_event()
                except Exception as e:
                    yield await FormatterService.format_error_event(e)

            elif model_type == MODEL_CLAUDE:
                # Format messages for Claude
                messages = []
                system_message = system_prompt

                for msg in request.messages:
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
                            print("Content:", content)  # Debug log
                            yield await FormatterService.format_streaming_chunk(content)

                    # Send done event
                    yield await FormatterService.format_done_event()
                except Exception as e:
                    yield await FormatterService.format_error_event(e)

            elif model_type == MODEL_TITAN:
                # Titan streaming with textGenerationConfig
                client = model_router.bedrock_client

                try:
                    async for chunk in client.generate_chat_completion_stream(
                        messages=request.messages,
                        model=request.model,
                        system=request.system_prompt,
                        max_tokens=request.max_tokens if hasattr(request, 'max_tokens') else DEFAULT_MAX_TOKENS,
                        inference_profile_arn=request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
                    ):
                        print("Raw chunk:", chunk)  # Debug log
                        if chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                            content = chunk["choices"][0]["delta"]["content"]
                            print("Content:", content)  # Debug log
                            yield await FormatterService.format_streaming_chunk(content)

                    # Send done event
                    yield await FormatterService.format_done_event()
                except Exception as e:
                    yield await FormatterService.format_error_event(e)

            elif model_type == MODEL_COHERE:
                # Cohere streaming
                client = model_router.bedrock_client

                # Format messages for Cohere
                messages = ChatService.prepare_cohere_request(request.messages)

                try:
                    async for chunk in client._stream_cohere_response(
                        request.model,
                        messages,
                        client._get_model_with_profile(
                            request.model,
                            request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
                        )
                    ):
                        if "generations" in chunk and len(chunk["generations"]) > 0:
                            if "text" in chunk["generations"][0]:
                                content = chunk["generations"][0]["text"]
                                yield await FormatterService.format_streaming_chunk(content)

                    # Send done event
                    yield await FormatterService.format_done_event()
                except Exception as e:
                    yield await FormatterService.format_error_event(e)

            elif model_type == MODEL_LLAMA:
                # Llama streaming
                client = model_router.bedrock_client

                # Format prompt for Llama
                prompt = ChatService.prepare_llama_request(request.messages)

                try:
                    async for chunk in client._stream_llama_response(
                        request.model,
                        prompt,
                        client._get_model_with_profile(
                            request.model,
                            request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
                        )
                    ):
                        if "generation" in chunk:
                            content = chunk["generation"]
                            yield await FormatterService.format_streaming_chunk(content)

                    # Send done event
                    yield await FormatterService.format_done_event()
                except Exception as e:
                    yield await FormatterService.format_error_event(e)

            elif model_type == MODEL_MISTRAL:
                # Mistral streaming
                print("Mistral streaming")
                client = model_router.bedrock_client

                try:
                    async for chunk in client.generate_chat_completion_stream(
                        messages=request.messages,
                        model=request.model,
                        system=request.system_prompt,
                        max_tokens=request.max_tokens if hasattr(request, 'max_tokens') else DEFAULT_MAX_TOKENS,
                        inference_profile_arn=request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
                    ):
                        print("Raw Mistral chunk:", chunk)  # Debug log
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            if "delta" in chunk["choices"][0] and "content" in chunk["choices"][0]["delta"]:
                                content = chunk["choices"][0]["delta"]["content"]
                                print("Mistral content:", content)  # Debug log
                                yield await FormatterService.format_streaming_chunk(content)

                    # Send done event
                    yield await FormatterService.format_done_event()
                except Exception as e:
                    print(f"Error in Mistral streaming: {e}")
                    import traceback
                    print(traceback.format_exc())
                    yield await FormatterService.format_error_event(e)

            else:
                # Unsupported model
                yield await FormatterService.format_error_event(
                    Exception(f"Unsupported model type: {request.model}")
                )

        except Exception as e:
            print(f"Error in generate function: {e}")
            yield await FormatterService.format_error_event(e)

    return EventSourceResponse(generate())
