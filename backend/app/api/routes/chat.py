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

router = APIRouter()

# System prompt to encourage proper markdown formatting
MARKDOWN_SYSTEM_PROMPT = """
You MUST format your responses using proper markdown formatting.

Rules for code blocks:
1. ALWAYS use triple backticks (```) to create code blocks, NEVER use single backticks for multi-line code.
2. ALWAYS specify the language immediately after the opening backticks (e.g., ```python, ```javascript, ```mermaid).
3. ALWAYS include a newline after the opening backticks with language and before the closing backticks.
4. NEVER nest code blocks inside other code blocks.
5. For Mermaid diagrams, always use ```mermaid as the language identifier.

Examples of CORRECT code block formatting:

```python
def hello_world():
    print("Hello, world!")
```

```javascript
function helloWorld() {
    console.log("Hello, world!");
}
```

```mermaid
graph TD
    A[Start] --> B[Process]
    B --> C[End]
```

Examples of INCORRECT code block formatting, you will be penalized if you follow these rules:

```
def hello_world():
    print("Hello, world!")
```

```python def hello_world():
    print("Hello, world!")```

`def hello_world():
    print("Hello, world!")`

For Mermaid diagrams:
1. Use proper Mermaid syntax for creating diagrams (flowcharts, sequence diagrams, gantt charts, etc.)
2. Always start with the diagram type (graph, sequenceDiagram, gantt, etc.)
3. Use proper indentation for readability

Other markdown formatting:
- Use # for main headings, ## for subheadings, etc.
- Use * or - for bullet points
- Use 1. 2. 3. for numbered lists
- Use > for blockquotes
- Use **text** for bold, *text* for italic
- Use [text](URL) for links
- Use ![alt text](URL) for images
- Use | tables | like | this | for tables with headers
"""

# Constants
WHITESPACE_CHARS = {' ', '\n', '\t'}

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

        # Handle messages based on model type
        messages = list(request.messages)
        system_content = None

        if request.model.startswith("anthropic.claude"):
            # For Anthropic models, system message needs to be handled differently
            system_content = MARKDOWN_SYSTEM_PROMPT
            non_system_messages = []
            for msg in messages:
                if msg.role == "system":
                    system_content += "\n\n" + msg.content
                else:
                    non_system_messages.append(msg)
            messages = non_system_messages
        else:
            # For other models like GPT, add system message if not present
            if not any(msg.role == "system" for msg in messages):
                messages.insert(0, Message(role="system", content=MARKDOWN_SYSTEM_PROMPT))

        # Route the request to the appropriate provider
        response = await model_router.route_chat_completion(
            messages=messages,
            model=request.model,
            system=system_content if request.model.startswith("anthropic.claude") else None,
            max_tokens=2000 if request.model.startswith("anthropic.claude") else None,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating chat completion: {str(e)}")

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    # Check if the stream flag is set
    if not request.stream:
        raise HTTPException(status_code=400, detail="Use /chat for non-streaming responses")

    async def generate():
        try:
            messages = list(request.messages)
            system_content = None

            if request.model.startswith("gpt"):
                # Add system message if not already present
                if not any(msg.role == "system" for msg in messages):
                    messages.insert(0, Message(role="system", content=MARKDOWN_SYSTEM_PROMPT))

                # Azure OpenAI streaming
                response = model_router.azure_client.client.chat.completions.create(
                    model=request.model,
                    messages=[{"role": msg.role, "content": msg.content} for msg in messages],
                    stream=True,
                    max_tokens=2000
                )

                try:
                    for chunk in response:
                        print("Raw chunk:", chunk)  # Debug log
                        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                            content = chunk.choices[0].delta.content
                            print("Content:", content)  # Debug log

                            # Format code blocks with proper newlines
                            # Check for code block markers
                            if "```" in content:
                                # If this is an opening code block marker
                                if content.strip().startswith("```") and not content.strip().endswith("```"):
                                    # Ensure there's a newline after the language identifier
                                    if not content.endswith('\n'):
                                        content += '\n'
                                # If this is a closing code block marker
                                elif content.strip() == "```" or content.strip().endswith("```"):
                                    # Ensure there's a newline before the closing marker
                                    if not content.startswith('\n'):
                                        content = '\n' + content
                                    # Ensure there's a newline after the closing marker
                                    if not content.endswith('\n'):
                                        content += '\n'

                            yield {
                                "event": "message",
                                "id": str(uuid.uuid4()),
                                "retry": 15000,  # 15s retry timeout
                                "data": json.dumps({"content": content})
                            }
                            await asyncio.sleep(0)  # Allow other tasks to run
                    # Send done event
                    yield {
                        "event": "done",
                        "id": str(uuid.uuid4()),
                        "retry": 15000,
                        "data": json.dumps({"content": "[DONE]"})
                    }
                except Exception as e:
                    yield {
                        "event": "error",
                        "id": str(uuid.uuid4()),
                        "retry": 15000,
                        "data": json.dumps({"error": f"Streaming error: {str(e)}"})
                    }

            elif request.model.startswith("anthropic.claude"):
                # Format messages for Claude
                messages = []
                system_message = MARKDOWN_SYSTEM_PROMPT

                for msg in request.messages:
                    if msg.role == "system":
                        system_message = msg.content + "\n\n" + MARKDOWN_SYSTEM_PROMPT
                    else:
                        messages.append(msg)

                # Format request body
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": request.max_tokens if hasattr(request, 'max_tokens') else 2000,
                    "temperature": request.temperature if hasattr(request, 'temperature') else 0.7,
                    "system": system_message,
                    "messages": [
                        {
                            "role": msg.role,
                            "content": [{"type": "text", "text": msg.content}]
                        }
                        for msg in messages
                    ]
                }

                # Get Claude response stream
                client = model_router.bedrock_client
                try:
                    async for chunk in client._stream_claude_response(request.model, request_body, client._get_model_with_profile(
                        request.model,
                        request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
                    )):
                        print("Raw chunk:", chunk)  # Debug log
                        if chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                            content = chunk["choices"][0]["delta"]["content"]
                            print("Content:", content)  # Debug log

                            # Format code blocks with proper newlines
                            # Check for code block markers
                            if "```" in content:
                                # If this is an opening code block marker
                                if content.strip().startswith("```") and not content.strip().endswith("```"):
                                    # Ensure there's a newline after the language identifier
                                    if not content.endswith('\n'):
                                        content += '\n'
                                # If this is a closing code block marker
                                elif content.strip() == "```" or content.strip().endswith("```"):
                                    # Ensure there's a newline before the closing marker
                                    if not content.startswith('\n'):
                                        content = '\n' + content
                                    # Ensure there's a newline after the closing marker
                                    if not content.endswith('\n'):
                                        content += '\n'

                            yield {
                                "event": "message",
                                "id": str(uuid.uuid4()),
                                "retry": 15000,
                                "data": json.dumps({"content": content})
                            }
                    # Send done event
                    yield {
                        "event": "done",
                        "id": str(uuid.uuid4()),
                        "retry": 15000,
                        "data": json.dumps({"content": "[DONE]"})
                    }
                except Exception as e:
                    yield {
                        "event": "error",
                        "id": str(uuid.uuid4()),
                        "retry": 15000,
                        "data": json.dumps({"error": f"Streaming error: {str(e)}"})
                    }

            elif request.model.startswith("amazon.titan"):
                # Titan streaming with textGenerationConfig
                client = model_router.bedrock_client

                # Convert messages to Titan format
                input_text = ""
                for msg in request.messages:
                    if msg.role == "user":
                        input_text += f"Human: {msg.content}\n"
                    elif msg.role == "assistant":
                        input_text += f"Assistant: {msg.content}\n"
                input_text += "Assistant: "

                request_body = {
                    "inputText": input_text,
                    "maxTokens": request.max_tokens if hasattr(request, 'max_tokens') else 2000,
                    "temperature": request.temperature if hasattr(request, 'temperature') else 0.7
                }

                try:
                    async for chunk in client._stream_titan_response(request.model, request_body, client._get_model_with_profile(
                        request.model,
                        request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
                    )):
                        print("Raw chunk:", chunk)  # Debug log
                        if chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                            content = chunk["choices"][0]["delta"]["content"]
                            print("Content:", content)  # Debug log

                            # Format code blocks with proper newlines
                            # Check for code block markers
                            if "```" in content:
                                # If this is an opening code block marker
                                if content.strip().startswith("```") and not content.strip().endswith("```"):
                                    # Ensure there's a newline after the language identifier
                                    if not content.endswith('\n'):
                                        content += '\n'
                                # If this is a closing code block marker
                                elif content.strip() == "```" or content.strip().endswith("```"):
                                    # Ensure there's a newline before the closing marker
                                    if not content.startswith('\n'):
                                        content = '\n' + content
                                    # Ensure there's a newline after the closing marker
                                    if not content.endswith('\n'):
                                        content += '\n'

                            yield {
                                "event": "message",
                                "id": str(uuid.uuid4()),
                                "retry": 15000,
                                "data": json.dumps({"content": content})
                            }
                    # Send done event
                    yield {
                        "event": "done",
                        "id": str(uuid.uuid4()),
                        "retry": 15000,
                        "data": json.dumps({"content": "[DONE]"})
                    }
                except Exception as e:
                    yield {
                        "event": "error",
                        "id": str(uuid.uuid4()),
                        "retry": 15000,
                        "data": json.dumps({"error": f"Streaming error: {str(e)}"})
                    }

            elif request.model.startswith("meta.llama"):
                # Add system message if not already present
                messages = list(request.messages)
                has_system = False
                for msg in messages:
                    if msg.role == "system":
                        has_system = True
                        # Append markdown formatting instructions to existing system message
                        msg.content += "\n\n" + MARKDOWN_SYSTEM_PROMPT
                        break

                if not has_system:
                    messages.insert(0, Message(role="system", content=MARKDOWN_SYSTEM_PROMPT))

                # Llama streaming with [INST] and <<SYS>> tags
                client = model_router.bedrock_client

                request_body = {
                    "messages": [
                        {
                            "role": msg.role,
                            "content": msg.content
                        }
                        for msg in messages
                    ],
                    "maxTokens": request.max_tokens if hasattr(request, 'max_tokens') else 2000,
                    "temperature": request.temperature if hasattr(request, 'temperature') else 0.7,
                    "topP": request.top_p if hasattr(request, 'top_p') else 0.9
                }

                try:
                    async for chunk in client._stream_llama_response(request.model, request_body, client._get_model_with_profile(
                        request.model,
                        request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
                    )):
                        print("Raw chunk:", chunk)  # Debug log
                        if chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                            content = chunk["choices"][0]["delta"]["content"]
                            print("Content:", content)  # Debug log

                            # Format code blocks with proper newlines
                            # Check for code block markers
                            if "```" in content:
                                # If this is an opening code block marker
                                if content.strip().startswith("```") and not content.strip().endswith("```"):
                                    # Ensure there's a newline after the language identifier
                                    if not content.endswith('\n'):
                                        content += '\n'
                                # If this is a closing code block marker
                                elif content.strip() == "```" or content.strip().endswith("```"):
                                    # Ensure there's a newline before the closing marker
                                    if not content.startswith('\n'):
                                        content = '\n' + content
                                    # Ensure there's a newline after the closing marker
                                    if not content.endswith('\n'):
                                        content += '\n'

                            yield {
                                "event": "message",
                                "id": str(uuid.uuid4()),
                                "retry": 15000,
                                "data": json.dumps({"content": content})
                            }
                    # Send done event
                    yield {
                        "event": "done",
                        "id": str(uuid.uuid4()),
                        "retry": 15000,
                        "data": json.dumps({"content": "[DONE]"})
                    }
                except Exception as e:
                    yield {
                        "event": "error",
                        "id": str(uuid.uuid4()),
                        "retry": 15000,
                        "data": json.dumps({"error": f"Streaming error: {str(e)}"})
                    }

            elif request.model.startswith("mistral"):
                # Add system message if not already present
                messages = list(request.messages)
                has_system = False
                for msg in messages:
                    if msg.role == "system":
                        has_system = True
                        # Append markdown formatting instructions to existing system message
                        msg.content += "\n\n" + MARKDOWN_SYSTEM_PROMPT
                        break

                if not has_system:
                    messages.insert(0, Message(role="system", content=MARKDOWN_SYSTEM_PROMPT))

                # Mistral streaming with [INST] tags
                client = model_router.bedrock_client

                request_body = {
                    "messages": [
                        {
                            "role": msg.role,
                            "content": msg.content
                        }
                        for msg in messages
                    ],
                    "maxTokens": request.max_tokens if hasattr(request, 'max_tokens') else 2000,
                    "temperature": request.temperature if hasattr(request, 'temperature') else 0.7,
                    "topP": request.top_p if hasattr(request, 'top_p') else 0.9,
                    "topK": request.top_k if hasattr(request, 'top_k') else 50
                }

                try:
                    async for chunk in client._stream_mistral_response(request.model, request_body, client._get_model_with_profile(
                        request.model,
                        request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
                    )):
                        print("Raw chunk:", chunk)  # Debug log
                        if chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                            content = chunk["choices"][0]["delta"]["content"]
                            print("Content:", content)  # Debug log

                            # Format code blocks with proper newlines
                            # Check for code block markers
                            if "```" in content:
                                # If this is an opening code block marker
                                if content.strip().startswith("```") and not content.strip().endswith("```"):
                                    # Ensure there's a newline after the language identifier
                                    if not content.endswith('\n'):
                                        content += '\n'
                                # If this is a closing code block marker
                                elif content.strip() == "```" or content.strip().endswith("```"):
                                    # Ensure there's a newline before the closing marker
                                    if not content.startswith('\n'):
                                        content = '\n' + content
                                    # Ensure there's a newline after the closing marker
                                    if not content.endswith('\n'):
                                        content += '\n'

                            yield {
                                "event": "message",
                                "id": str(uuid.uuid4()),
                                "retry": 15000,
                                "data": json.dumps({"content": content})
                            }
                    # Send done event
                    yield {
                        "event": "done",
                        "id": str(uuid.uuid4()),
                        "retry": 15000,
                        "data": json.dumps({"content": "[DONE]"})
                    }
                except Exception as e:
                    yield {
                        "event": "error",
                        "id": str(uuid.uuid4()),
                        "retry": 15000,
                        "data": json.dumps({"error": f"Streaming error: {str(e)}"})
                    }

            elif request.model.startswith("meta.ai21"):
                # Add system message if not already present
                messages = list(request.messages)
                has_system = False
                for msg in messages:
                    if msg.role == "system":
                        has_system = True
                        # Append markdown formatting instructions to existing system message
                        msg.content += "\n\n" + MARKDOWN_SYSTEM_PROMPT
                        break

                if not has_system:
                    messages.insert(0, Message(role="system", content=MARKDOWN_SYSTEM_PROMPT))

                # AI21 streaming with [INST] tags
                client = model_router.bedrock_client

                request_body = {
                    "messages": [
                        {
                            "role": msg.role,
                            "content": msg.content
                        }
                        for msg in messages
                    ],
                    "maxTokens": request.max_tokens if hasattr(request, 'max_tokens') else 2000,
                    "temperature": request.temperature if hasattr(request, 'temperature') else 0.7,
                    "topP": request.top_p if hasattr(request, 'top_p') else 0.9,
                    "topK": request.top_k if hasattr(request, 'top_k') else 50
                }

                try:
                    async for chunk in client._stream_ai21_response(request.model, request_body, client._get_model_with_profile(
                        request.model,
                        request.inference_profile_arn if hasattr(request, 'inference_profile_arn') else None
                    )):
                        print("Raw chunk:", chunk)  # Debug log
                        if chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                            content = chunk["choices"][0]["delta"]["content"]
                            print("Content:", content)  # Debug log

                            # Format code blocks with proper newlines
                            # Check for code block markers
                            if "```" in content:
                                # If this is an opening code block marker
                                if content.strip().startswith("```") and not content.strip().endswith("```"):
                                    # Ensure there's a newline after the language identifier
                                    if not content.endswith('\n'):
                                        content += '\n'
                                # If this is a closing code block marker
                                elif content.strip() == "```" or content.strip().endswith("```"):
                                    # Ensure there's a newline before the closing marker
                                    if not content.startswith('\n'):
                                        content = '\n' + content
                                    # Ensure there's a newline after the closing marker
                                    if not content.endswith('\n'):
                                        content += '\n'

                            # Add a space after each chunk if it doesn't end with whitespace
                            # This helps with word boundaries when streaming
                            if content and not content[-1] in WHITESPACE_CHARS:
                                content += ' '

                            yield {
                                "event": "message",
                                "id": str(uuid.uuid4()),
                                "retry": 15000,
                                "data": json.dumps({"content": content})
                            }
                    # Send done event
                    yield {
                        "event": "done",
                        "id": str(uuid.uuid4()),
                        "retry": 15000,
                        "data": json.dumps({"content": "[DONE]"})
                    }
                except Exception as e:
                    yield {
                        "event": "error",
                        "id": str(uuid.uuid4()),
                        "retry": 15000,
                        "data": json.dumps({"error": f"Streaming error: {str(e)}"})
                    }

            else:
                # For other models (Mistral), simulate streaming
                try:
                    # Add system message if not already present
                    messages = list(request.messages)
                    has_system = False
                    for msg in messages:
                        if msg.role == "system":
                            has_system = True
                            # Append markdown formatting instructions to existing system message
                            msg.content += "\n\n" + MARKDOWN_SYSTEM_PROMPT
                            break

                    if not has_system:
                        messages.insert(0, Message(role="system", content=MARKDOWN_SYSTEM_PROMPT))

                    response = await chat(request)
                    content = response.choices[0].message.content

                    # Stream in small chunks
                    for i in range(0, len(content), 4):
                        chunk = content[i:i+4]
                        # Format code blocks with proper newlines
                        # Check for code block markers
                        if "```" in chunk:
                            # If this is an opening code block marker
                            if chunk.strip().startswith("```") and not chunk.strip().endswith("```"):
                                # Ensure there's a newline after the language identifier
                                if not chunk.endswith('\n'):
                                    chunk += '\n'
                            # If this is a closing code block marker
                            elif chunk.strip() == "```" or chunk.strip().endswith("```"):
                                # Ensure there's a newline before the closing marker
                                if not chunk.startswith('\n'):
                                    chunk = '\n' + chunk
                                # Ensure there's a newline after the closing marker
                                if not chunk.endswith('\n'):
                                    chunk += '\n'

                        # Add a space after each chunk if it doesn't end with whitespace
                        # This helps with word boundaries when streaming
                        if chunk and not chunk[-1] in WHITESPACE_CHARS:
                            chunk += ' '

                        yield {
                            "event": "message",
                            "id": str(uuid.uuid4()),
                            "retry": 15000,
                            "data": json.dumps({"content": chunk})
                        }
                        await asyncio.sleep(0.01)
                    # Send done event
                    yield {
                        "event": "done",
                        "id": str(uuid.uuid4()),
                        "retry": 15000,
                        "data": json.dumps({"content": "[DONE]"})
                    }
                except Exception as e:
                    yield {
                        "event": "error",
                        "id": str(uuid.uuid4()),
                        "retry": 15000,
                        "data": json.dumps({"error": f"Streaming error: {str(e)}"})
                    }

        except Exception as e:
            yield {
                "event": "error",
                "id": str(uuid.uuid4()),
                "retry": 15000,
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(generate())
