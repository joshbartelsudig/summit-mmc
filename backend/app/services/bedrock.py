import json
import boto3
import os
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple, Union
from botocore.exceptions import ClientError
import time
import uuid
import asyncio
import traceback
from app.core.config import settings
from app.models.schemas import ChatMessage

class BedrockClient:
    """Client for Amazon Bedrock API interactions"""

    # Default mapping of models to inference profiles
    # This allows us to automatically use the correct inference profile for each model
    DEFAULT_INFERENCE_PROFILES = {
        # Claude models
        "anthropic.claude-3-haiku-20240307-v1:0": "arn:aws:bedrock:us-east-1:105300344984:inference-profile/us.anthropic.claude-3-haiku-20240307-v1:0",
        "anthropic.claude-3-opus-20240229-v1:0": "arn:aws:bedrock:us-east-1:105300344984:inference-profile/us.anthropic.claude-3-opus-20240229-v1:0",
        "anthropic.claude-3-sonnet-20240229-v1:0": "arn:aws:bedrock:us-east-1:105300344984:inference-profile/us.anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-5-haiku-20241022-v1:0": "arn:aws:bedrock:us-east-1:105300344984:inference-profile/us.anthropic.claude-3-5-haiku-20241022-v1:0",
        "anthropic.claude-3-5-sonnet-20240620-v1:0": "arn:aws:bedrock:us-east-1:105300344984:inference-profile/us.anthropic.claude-3-5-sonnet-20240620-v1:0",
        "anthropic.claude-3-5-sonnet-20241022-v2:0": "arn:aws:bedrock:us-east-1:105300344984:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "anthropic.claude-3-7-sonnet-20250219-v1:0": "arn:aws:bedrock:us-east-1:105300344984:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0",

        # DeepSeek model
        "deepseek.deepseek-coder-v1:0": "arn:aws:bedrock:us-east-1:105300344984:inference-profile/us.deepseek.r1-v1:0",

        # Meta Llama models
        "meta.llama3-3-70b-instruct-v1:0": "arn:aws:bedrock:us-east-1:105300344984:inference-profile/us.meta.llama3-3-70b-instruct-v1:0",
        "meta.llama3-3-8b-instruct-v1:0": "arn:aws:bedrock:us-east-1:105300344984:inference-profile/us.meta.llama3-3-8b-instruct-v1:0"
    }

    def __init__(self):
        """Initialize the Amazon Bedrock client"""
        self.region = settings.AWS_REGION

        # Get AWS credentials from environment variables
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

        print(f"AWS Region: {self.region}")
        print(f"AWS Access Key ID available: {bool(aws_access_key)}")

        # Initialize boto3 session with credentials
        try:
            self.session = boto3.Session(
                region_name=self.region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )

            # Initialize Bedrock Runtime client for model inference
            self.runtime = self.session.client(
                service_name="bedrock-runtime",
                region_name=self.region,
            )

            # Initialize Bedrock client for listing models
            self.bedrock = self.session.client(
                service_name="bedrock",
                region_name=self.region,
            )
            print("Successfully initialized Bedrock clients")
        except Exception as e:
            print(f"Error initializing Bedrock clients: {str(e)}")
            self.runtime = None
            self.bedrock = None

    def check_model_access(self, model_id: str) -> bool:
        """
        Check if the current AWS account has access to a specific model

        Args:
            model_id (str): The Bedrock model ID to check

        Returns:
            bool: True if the model is accessible, False otherwise
        """
        try:
            if not self.runtime:
                return False

            # For specific models we know are available from the screenshot, return true
            # This helps us avoid unnecessary API calls for models we know should be available
            known_available_models = [
                "meta.llama3-3-70b-instruct-v1:0",
                "anthropic.claude-3-7-sonnet-20250219-v1:0",
                "anthropic.claude-3-5-haiku-20241022-v1:0",
                "anthropic.claude-3-5-sonnet-20241022-v2:0",
                "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "amazon.titan-text-lite-v1",
                "amazon.titan-text-premier-v1:0",
                "mistral.mistral-7b-instruct-v0:2"
            ]

            if model_id in known_available_models:
                return True

            # Prepare a minimal test request based on the model family
            if model_id.startswith("anthropic.claude"):
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Hello"
                                }
                            ]
                        }
                    ]
                }
            elif model_id.startswith("amazon.titan"):
                request_body = {
                    "inputText": "Human: Hello\nAssistant: ",
                    "textGenerationConfig": {
                        "maxTokenCount": 1,
                        "temperature": 0.7,
                        "topP": 0.9,
                        "stopSequences": []
                    }
                }
            elif model_id.startswith("meta.llama"):
                request_body = {
                    "prompt": "<human>\nHello\n</human>\n<assistant>\n",
                    "max_gen_len": 1,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            elif model_id.startswith("mistral.mistral"):
                request_body = {
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 1,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            else:
                # For unknown model families, use a generic approach
                request_body = {"prompt": "Hello", "max_tokens": 1}

            # Try to invoke the model with a minimal request
            # We don't care about the response, just whether it succeeds
            self.runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )

            # If we get here, we have access to the model
            return True
        except Exception as e:
            error_str = str(e)
            if "AccessDeniedException" in error_str:
                print(f"Access denied for model {model_id}: {error_str}")
                return False
            elif "ValidationException" in error_str:
                # Check for specific validation errors that indicate we don't have proper access
                if "inference profile" in error_str.lower() or "isn't supported" in error_str.lower():
                    print(f"Model {model_id} requires an inference profile: {error_str}")
                    return False
                else:
                    # Other validation errors might be due to our test request format
                    print(f"Validation error for model {model_id}: {error_str}")
                    return True
            else:
                print(f"Error checking access for model {model_id}: {error_str}")
                return False

    def bulk_check_model_access(self, model_ids: List[str]) -> Dict[str, bool]:
        """
        Check access for multiple models in bulk

        Args:
            model_ids (List[str]): List of model IDs to check

        Returns:
            Dict[str, bool]: Dictionary mapping model IDs to access status
        """
        results = {}
        for model_id in model_ids:
            results[model_id] = self.check_model_access(model_id)
        return results

    def list_models(self, use_cache=True) -> List[Dict[str, Any]]:
        """
        List available models from Amazon Bedrock

        Args:
            use_cache (bool): Whether to use cached models if available

        Returns:
            List[Dict[str, Any]]: List of available models
        """
        # Return cached models if available and cache is enabled
        if use_cache and hasattr(self, '_cached_models') and self._cached_models:
            print("Using cached Bedrock models")
            return self._cached_models

        try:
            if self.bedrock:
                print("Attempting to list Bedrock models...")
                try:
                    # Get foundation models from the API
                    print("Calling list_foundation_models API...")
                    response = self.bedrock.list_foundation_models()

                    # Format the response to match our API format
                    all_models = []
                    for model in response.get('modelSummaries', []):
                        model_id = model.get('modelId')
                        all_models.append({
                            "id": model_id,
                            "provider": "bedrock",
                            "name": model.get('modelName', model_id)
                        })

                    # Filter to a subset of models we want to try
                    # We'll focus on text models that are commonly used
                    test_models = []
                    for model in all_models:
                        model_id = model["id"]
                        if any([
                            model_id.startswith("anthropic.claude"),
                            model_id.startswith("amazon.titan-text"),
                            model_id.startswith("meta.llama"),
                            model_id.startswith("mistral.mistral"),
                            model_id.startswith("amazon.titan-tg1"),
                            # Add other model families you want to test
                        ]):
                            test_models.append(model)

                    print(f"Testing access for {len(test_models)} Bedrock models...")

                    # Get model IDs to check
                    model_ids_to_check = [model["id"] for model in test_models]

                    # Check access in bulk
                    access_results = self.bulk_check_model_access(model_ids_to_check)

                    # Filter to accessible models
                    accessible_models = []
                    for model in test_models:
                        model_id = model["id"]
                        if access_results.get(model_id, False):
                            print(f"✅ Access confirmed for model: {model_id}")
                            accessible_models.append(model)
                        else:
                            print(f"❌ No access to model: {model_id}")

                    print(f"Found {len(accessible_models)} accessible Bedrock models")

                    if accessible_models:
                        # Cache the models for future use
                        self._cached_models = accessible_models
                        return accessible_models
                    else:
                        print("No accessible Bedrock models found, using fallback models")
                        return self._get_fallback_models()
                except Exception as e:
                    print(f"Error in Bedrock API call: {str(e)}")
                    return self._get_fallback_models()
            else:
                print("Bedrock client not initialized, using fallback models")
                return self._get_fallback_models()
        except Exception as e:
            print(f"Unexpected error listing Bedrock models: {str(e)}")
            return self._get_fallback_models()

    def _get_fallback_models(self) -> List[Dict[str, Any]]:
        """
        Return fallback models when API calls fail

        Returns:
            List[Dict[str, Any]]: List of fallback models
        """
        # These are just a few common models as fallbacks
        fallback_models = [
            {"id": "anthropic.claude-3-sonnet-20240229-v1:0", "provider": "bedrock", "name": "Claude 3 Sonnet"},
            {"id": "amazon.titan-text-express-v1", "provider": "bedrock", "name": "Titan Text Express"},
            {"id": "mistral.mistral-7b-instruct-v0:2", "provider": "bedrock", "name": "Mistral 7B Instruct"}
        ]

        # Cache these fallback models
        self._cached_models = fallback_models
        return fallback_models

    def _get_role_and_content(self, msg: Union[Dict[str, Any], ChatMessage]) -> Tuple[str, str]:
        """Get role and content from a message object"""
        if isinstance(msg, dict):
            return msg["role"], msg["content"]
        return msg.role, msg.content

    def _format_messages_for_mistral(self, messages: List[Union[Dict[str, Any], ChatMessage]]) -> str:
        """Format messages for Mistral models"""
        formatted_messages = []
        for msg in messages:
            role, content = self._get_role_and_content(msg)
            if role == "system":
                formatted_messages.append(f"[INST] <<SYS>>\n{content}\n<</SYS>> [/INST]")
            elif role == "user":
                formatted_messages.append(f"[INST] {content} [/INST]")
            elif role == "assistant":
                formatted_messages.append(content)
        return "\n".join(formatted_messages)

    def _format_messages_for_llama(self, messages: List[Union[Dict[str, Any], ChatMessage]]) -> str:
        """Format messages for Llama models"""
        formatted_messages = []
        for msg in messages:
            role, content = self._get_role_and_content(msg)
            if role == "system":
                formatted_messages.append(f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{content}<|eot_id|>")
            elif role == "user":
                formatted_messages.append(f"<|start_header_id|>user<|end_header_id|>\n{content}<|eot_id|>")
            elif role == "assistant":
                formatted_messages.append(f"<|start_header_id|>assistant<|end_header_id|>\n{content}<|eot_id|>")

        # Add <|begin_of_text|> at the start if there's no system message
        if not any(isinstance(msg, dict) and msg.get("role") == "system" or isinstance(msg, ChatMessage) and msg.role == "system" for msg in messages):
            formatted_messages.insert(0, "<|begin_of_text|>")

        # Add assistant header for the response
        formatted_messages.append("<|start_header_id|>assistant<|end_header_id|>")
        return "\n".join(formatted_messages)

    def _format_messages_for_titan(self, messages: List[Union[Dict[str, Any], ChatMessage]]) -> str:
        """Format messages for Titan models"""
        formatted_messages = []
        system_messages = []
        
        # First, extract system messages
        for msg in messages:
            role, content = self._get_role_and_content(msg)
            if role == "system":
                system_messages.append(f"System: {content}")
        
        # Add all system messages at the beginning
        if system_messages:
            formatted_messages.extend(system_messages)
            # Add an empty line after system messages for better separation
            formatted_messages.append("")
        
        # Then add user and assistant messages
        for msg in messages:
            role, content = self._get_role_and_content(msg)
            if role == "user":
                formatted_messages.append(f"Human: {content}")
            elif role == "assistant":
                formatted_messages.append(f"Assistant: {content}")
        
        return "\n".join(formatted_messages) + "\nAssistant: "

    def _format_messages_for_claude(self, messages: List[Union[Dict[str, Any], ChatMessage]]) -> Tuple[str, List[Dict[str, Any]]]:
        """Format messages for Claude models"""
        formatted_messages = []
        system_message = None
        
        for msg in messages:
            role, content = self._get_role_and_content(msg)
            if role == "system":
                system_message = content
            elif content.strip():  # Only add non-empty messages
                formatted_messages.append({
                    "role": role,
                    "content": [{"type": "text", "text": content}]
                })
        
        return system_message, formatted_messages

    def _get_model_with_profile(self, model_id: str, inference_profile_arn: Optional[str] = None) -> str:
        """
        Get the correct model ID to use, which might be an inference profile ARN

        Args:
            model_id (str): The original model ID
            inference_profile_arn (Optional[str]): The inference profile ARN if provided

        Returns:
            str: The model ID to use (which might be the inference profile ARN)
        """
        # If an inference profile ARN is explicitly provided, use it
        if inference_profile_arn:
            print(f"DEBUG: Using provided inference profile ARN: {inference_profile_arn}")
            return inference_profile_arn

        # Check if there's a default inference profile for this model
        if model_id in self.DEFAULT_INFERENCE_PROFILES:
            profile_arn = self.DEFAULT_INFERENCE_PROFILES[model_id]
            print(f"DEBUG: Using default inference profile ARN for {model_id}: {profile_arn}")
            return profile_arn

        # No inference profile found, use the original model ID
        print(f"DEBUG: No inference profile found for {model_id}, using original model ID")
        return model_id

    def _invoke_claude(self, model: str, messages: List[Union[Dict[str, Any], ChatMessage]], max_tokens: Optional[int] = None, inference_profile_arn: Optional[str] = None, system: Optional[str] = None) -> Dict[str, Any]:
        """Invoke Claude models"""
        # Get system message and formatted messages
        system_message, formatted_messages = self._format_messages_for_claude(messages)
        
        # Format request body
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens or 2000,
            "messages": formatted_messages
        }

        # Add system message if provided in either way
        if system:
            request_body["system"] = system
        elif system_message:
            request_body["system"] = system_message

        # Add request body to invoke parameters
        invoke_params = {
            "modelId": model,
            "body": json.dumps(request_body),
            "contentType": "application/json",
            "accept": "application/json"
        }

        # Invoke the model
        response = self.runtime.invoke_model(**invoke_params)

        # Parse the response
        response_body = json.loads(response.get('body').read())
        completion = response_body.get('content', [{}])[0].get('text', '')

        return {
            "id": f"bedrock-{model}-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": completion
                    },
                    "finish_reason": "stop",
                    "index": 0
                }
            ]
        }

    async def generate_chat_completion(
        self, messages: List[Union[Dict[str, Any], ChatMessage]], model: str, system: Optional[str] = None, max_tokens: Optional[int] = None, inference_profile_arn: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using Amazon Bedrock

        Args:
            messages (List[Union[Dict[str, Any], ChatMessage]]): List of chat messages
            model (str): Model ID
            system (Optional[str]): System message
            max_tokens (Optional[int]): Maximum number of tokens
            inference_profile_arn (Optional[str]): ARN of the inference profile to use (for models that require it)

        Returns:
            Dict[str, Any]: Chat completion response
        """
        try:
            if not messages:
                raise Exception("No messages provided")

            if not self.runtime:
                raise Exception("Bedrock runtime client not initialized")

            # Get the correct model ID to use (which might be the inference profile ARN)
            model_to_use = self._get_model_with_profile(model, inference_profile_arn)
            print(f"DEBUG: Using model ID for invocation: {model_to_use}")

            # Different models require different request formats
            if model.startswith("anthropic.claude"):
                # Format for Claude models
                return self._invoke_claude(model_to_use, messages, max_tokens, None, system)

            elif model.startswith("amazon.titan"):
                # Format for Titan models
                request_body = {
                    "inputText": self._format_messages_for_titan(messages),
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens or 2000,
                        "temperature": 0.7,
                        "topP": 0.9,
                        "stopSequences": []
                    }
                }

                # Add request body to invoke parameters
                invoke_params = {
                    "modelId": model_to_use,
                    "body": json.dumps(request_body),
                    "contentType": "application/json",
                    "accept": "application/json"
                }

                # Invoke the model
                response = self.runtime.invoke_model(**invoke_params)

                # Parse the response
                response_body = json.loads(response.get('body').read())
                completion = response_body.get('results', [{}])[0].get('outputText', '')

                return {
                    "id": f"bedrock-{model}-{uuid.uuid4()}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": completion
                            },
                            "finish_reason": "stop",
                            "index": 0
                        }
                    ]
                }

            elif model.startswith("meta.llama"):
                # Format for Llama models
                request_body = {
                    "prompt": self._format_messages_for_llama(messages),
                    "max_gen_len": max_tokens or 2000,
                    "temperature": 0.7,
                    "top_p": 0.9
                }

                # Add request body to invoke parameters
                invoke_params = {
                    "modelId": model_to_use,
                    "body": json.dumps(request_body),
                    "contentType": "application/json",
                    "accept": "application/json"
                }

                # Invoke the model
                response = self.runtime.invoke_model(**invoke_params)

                # Parse the response
                response_body = json.loads(response.get('body').read())
                completion = response_body.get('generation', '')

                return {
                    "id": f"bedrock-{model}-{uuid.uuid4()}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": completion
                            },
                            "finish_reason": response_body.get('stop_reason', 'stop'),
                            "index": 0
                        }
                    ]
                }

            elif model.startswith("mistral.mistral"):
                # Format for Mistral models
                request_body = {
                    "prompt": self._format_messages_for_mistral(messages),
                    "max_tokens": max_tokens or 2000,
                    "temperature": 0.7,
                    "top_p": 0.9
                }

                # Add request body to invoke parameters
                invoke_params = {
                    "modelId": model_to_use,
                    "body": json.dumps(request_body),
                    "contentType": "application/json",
                    "accept": "application/json"
                }

                # Invoke the model
                response = self.runtime.invoke_model(**invoke_params)

                # Parse the response
                response_body = json.loads(response.get('body').read())
                completion = response_body.get('outputs', [{}])[0].get('text', '')

                return {
                    "id": f"bedrock-{model}-{uuid.uuid4()}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": completion
                            },
                            "finish_reason": "stop",
                            "index": 0
                        }
                    ]
                }

            else:
                raise ValueError(f"Unsupported model: {model}")

        except Exception as e:
            error_str = str(e)
            print(f"Error generating Bedrock chat completion: {error_str}")

            if "ValidationException" in error_str and ("inference profile" in error_str.lower() or "isn't supported" in error_str.lower()):
                # This is a special case for models that require inference profiles
                print(f"Model {model} requires an inference profile")

                # Check if we have a mapping for this model
                if model in self.DEFAULT_INFERENCE_PROFILES:
                    profile_arn = self.DEFAULT_INFERENCE_PROFILES[model]
                    print(f"Using default inference profile: {profile_arn}")

                    # Try again with the inference profile
                    try:
                        return await self.generate_chat_completion(messages, model, system, max_tokens, profile_arn)
                    except Exception as retry_error:
                        print(f"Retry with inference profile failed: {str(retry_error)}")
                        error_message = f"Failed to use model {model} with inference profile {profile_arn}: {str(retry_error)}"
                        raise ValueError(error_message)
                else:
                    # We don't have a mapping for this model
                    error_message = f"Model {model} requires an inference profile and is not available for on-demand use. Please create an inference profile in AWS Bedrock and provide the ARN."
                    raise ValueError(error_message)
            elif "AccessDeniedException" in error_str:
                # This is a case where the user doesn't have access to the model
                print(f"Access denied for model {model}")

                # Check if this might be an inference profile issue
                if model.startswith("meta.llama") or model.startswith("anthropic.claude"):
                    error_message = f"Access denied for model {model}. This model may require an inference profile. Please check your AWS Bedrock permissions and ensure you have the correct inference profile configured."
                else:
                    error_message = f"Access denied for model {model}. Please check your AWS Bedrock permissions."

                raise ValueError(error_message)
            else:
                # For other errors, just pass through
                raise

    async def _stream_claude_response(self, model: str, request_body: Dict[str, Any], inference_profile_arn: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response from Claude models"""
        try:
            # Get the correct model ID to use (which might be the inference profile ARN)
            model_to_use = self._get_model_with_profile(model, inference_profile_arn)

            # Add anthropic version to request body if not present
            if "anthropic_version" not in request_body:
                request_body["anthropic_version"] = "bedrock-2023-05-31"

            # Invoke the model with streaming
            invoke_params = {
                "modelId": model_to_use,
                "body": json.dumps(request_body),
                "contentType": "application/json",
                "accept": "application/json"
            }

            response = self.runtime.invoke_model_with_response_stream(**invoke_params)

            # Get response content type
            content_type = response.get("ResponseMetadata", {}).get("HTTPHeaders", {}).get("x-amzn-bedrock-content-type")
            print(f"DEBUG: Response content type: {content_type}")

            # Process the streaming response
            stream = response.get('body')
            for event in stream:
                if 'chunk' in event:
                    chunk_data = json.loads(event['chunk']['bytes'].decode())

                    # Handle content block deltas (text)
                    if chunk_data['type'] == 'content_block_delta':
                        if 'text' in chunk_data['delta']:
                            yield {
                                "id": f"bedrock-{model}-{uuid.uuid4()}",
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": model,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {
                                            "content": chunk_data['delta']['text']
                                        },
                                        "finish_reason": None
                                    }
                                ]
                            }
                    # Handle message deltas (stop reason)
                    elif chunk_data['type'] == 'message_delta':
                        if 'stop_reason' in chunk_data['delta']:
                            yield {
                                "id": f"bedrock-{model}-{uuid.uuid4()}",
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": model,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {},
                                        "finish_reason": "stop"
                                    }
                                ]
                            }

        except Exception as e:
            error_str = str(e)
            print(f"Error streaming Claude response: {str(e)}")

            if "ValidationException" in error_str and ("inference profile" in error_str.lower() or "isn't supported" in error_str.lower()):
                # This is a special case for models that require inference profiles
                print(f"Model {model} requires an inference profile")

                # Check if we have a mapping for this model
                if model in self.DEFAULT_INFERENCE_PROFILES:
                    profile_arn = self.DEFAULT_INFERENCE_PROFILES[model]
                    print(f"Using default inference profile: {profile_arn}")

                    # Try again with the inference profile
                    try:
                        async for chunk in self._stream_claude_response(model, request_body, profile_arn):
                            yield chunk
                    except Exception as retry_error:
                        print(f"Retry with inference profile failed: {str(retry_error)}")
                        error_message = f"Failed to use model {model} with inference profile {profile_arn}: {str(retry_error)}"
                        raise ValueError(error_message)
                else:
                    # We don't have a mapping for this model
                    error_message = f"Model {model} requires an inference profile and is not available for on-demand use. Please create an inference profile in AWS Bedrock and provide the ARN."
                    raise ValueError(error_message)
            elif "AccessDeniedException" in error_str:
                # This is a case where the user doesn't have access to the model
                print(f"Access denied for model {model}")

                # Check if this might be an inference profile issue
                if model.startswith("meta.llama") or model.startswith("anthropic.claude"):
                    error_message = f"Access denied for model {model}. This model may require an inference profile. Please check your AWS Bedrock permissions and ensure you have the correct inference profile configured."
                else:
                    error_message = f"Access denied for model {model}. Please check your AWS Bedrock permissions."

                raise ValueError(error_message)
            else:
                # For other errors, just pass through
                import traceback
                print(traceback.format_exc())
                raise

    async def _stream_titan_response(self, model: str, request_body: Dict[str, Any], inference_profile_arn: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response from Titan models"""
        try:
            # Get the correct model ID to use (which might be the inference profile ARN)
            model_to_use = self._get_model_with_profile(model, inference_profile_arn)
            print(f"DEBUG: Using explicitly provided inference profile ARN: {model_to_use}")

            # Format the request using Titan's native structure
            native_request = {
                "inputText": self._format_messages_for_titan(request_body.get("messages", [])),
                "textGenerationConfig": {
                    "maxTokenCount": request_body.get("max_tokens", 2000),
                    "temperature": request_body.get("temperature", 0.7),
                    "topP": request_body.get("top_p", 0.9),
                    "stopSequences": []
                }
            }

            # Invoke the model with streaming
            invoke_params = {
                "modelId": model_to_use,
                "body": json.dumps(native_request),
                "contentType": "application/json",
                "accept": "application/json"
            }

            response = self.runtime.invoke_model_with_response_stream(**invoke_params)

            # Get response content type
            content_type = response.get("ResponseMetadata", {}).get("HTTPHeaders", {}).get("x-amzn-bedrock-content-type")
            print(f"DEBUG: Response content type: {content_type}")

            # Process the streaming response
            stream = response.get('body')
            for event in stream:
                if 'chunk' in event:
                    chunk_data = json.loads(event['chunk']['bytes'].decode())
                    print(f"DEBUG: Titan chunk: {chunk_data}")

                    # Format the chunk to match OpenAI's format
                    if 'outputText' in chunk_data:
                        yield {
                            "id": f"bedrock-{model}-{uuid.uuid4()}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "content": chunk_data['outputText']
                                    },
                                    "finish_reason": None
                                }
                            ]
                        }
                    elif 'completionReason' in chunk_data:
                        yield {
                            "id": f"bedrock-{model}-{uuid.uuid4()}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {},
                                    "finish_reason": "stop"
                                }
                            ]
                        }

        except Exception as e:
            print(f"Error streaming Titan response: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise

    async def _stream_llama_response(self, model: str, request_body: Dict[str, Any], inference_profile_arn: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response from Llama models"""
        try:
            # Get the correct model ID to use (which might be the inference profile ARN)
            model_to_use = self._get_model_with_profile(model, inference_profile_arn)

            # Format the request
            native_request = {
                "prompt": self._format_messages_for_llama(request_body.get("messages", [])),
                "temperature": request_body.get("temperature", 0.7),
                "top_p": request_body.get("top_p", 0.9),
                "max_gen_len": request_body.get("max_tokens", 512)
            }

            # Invoke the model with streaming
            invoke_params = {
                "modelId": model_to_use,
                "body": json.dumps(native_request),
                "contentType": "application/json",
                "accept": "application/json"
            }

            response = self.runtime.invoke_model_with_response_stream(**invoke_params)

            # Get response content type
            content_type = response.get("ResponseMetadata", {}).get("HTTPHeaders", {}).get("x-amzn-bedrock-content-type")
            print(f"DEBUG: Response content type: {content_type}")

            # Process the streaming response
            stream = response.get('body')
            for event in stream:
                if 'chunk' in event:
                    chunk_data = json.loads(event['chunk']['bytes'].decode())
                    print(f"DEBUG: Llama chunk: {chunk_data}")

                    # Format the chunk to match OpenAI's format
                    if 'generation' in chunk_data:
                        yield {
                            "id": f"bedrock-{model}-{uuid.uuid4()}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "content": chunk_data['generation']
                                    },
                                    "finish_reason": None
                                }
                            ]
                        }
                    elif 'stop_reason' in chunk_data:
                        yield {
                            "id": f"bedrock-{model}-{uuid.uuid4()}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {},
                                    "finish_reason": chunk_data['stop_reason']
                                }
                            ]
                        }

        except Exception as e:
            print(f"Error streaming Llama response: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise

    async def _stream_mistral_response(self, model: str, request_body: Dict[str, Any], inference_profile_arn: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response from Mistral models"""
        try:
            # Get the correct model ID to use (which might be the inference profile ARN)
            model_to_use = self._get_model_with_profile(model, inference_profile_arn)

            # Format messages with [INST] tags for Mistral
            formatted_prompt = ""
            for msg in request_body["messages"]:
                if msg["role"] == "user":
                    formatted_prompt += f"<s>[INST] {msg['content']} [/INST]"
                elif msg["role"] == "assistant":
                    formatted_prompt += f"{msg['content']}"

            # Format the request using Mistral's native structure
            native_request = {
                "prompt": formatted_prompt,
                "max_tokens": request_body.get("max_tokens", 2000),
                "temperature": request_body.get("temperature", 0.7),
                "top_p": request_body.get("top_p", 0.9)
            }

            # Invoke the model with streaming
            invoke_params = {
                "modelId": model_to_use,
                "body": json.dumps(native_request),
                "contentType": "application/json",
                "accept": "application/json"
            }

            response = self.runtime.invoke_model_with_response_stream(**invoke_params)

            # Get response content type
            content_type = response.get("ResponseMetadata", {}).get("HTTPHeaders", {}).get("x-amzn-bedrock-content-type")
            print(f"DEBUG: Response content type: {content_type}")

            # Process the streaming response
            stream = response.get('body')
            for event in stream:
                if 'chunk' in event:
                    chunk_data = json.loads(event['chunk']['bytes'].decode())

                    # Format the chunk to match OpenAI's format
                    if 'outputs' in chunk_data and chunk_data['outputs']:
                        text = chunk_data['outputs'][0].get('text', '')
                        if text:
                            yield {
                                "id": f"bedrock-{model}-{uuid.uuid4()}",
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": model,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {
                                            "content": text
                                        },
                                        "finish_reason": None
                                    }
                                ]
                            }
        except Exception as e:
            print(f"Error streaming Mistral response: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise

    async def generate_chat_completion_stream(
        self, messages: List[Union[Dict[str, Any], ChatMessage]], model: str, system: Optional[str] = None, max_tokens: Optional[int] = None, inference_profile_arn: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a streaming chat completion using Amazon Bedrock

        Args:
            messages (List[Union[Dict[str, Any], ChatMessage]]): List of chat messages
            model (str): Model ID
            system (Optional[str]): System message
            max_tokens (Optional[int]): Maximum number of tokens
            inference_profile_arn (Optional[str]): ARN of the inference profile to use (for models that require it)

        Returns:
            AsyncGenerator[Dict[str, Any], None]: Streaming chat completion response
        """
        try:
            # Get the correct model ID to use (which might be the inference profile ARN)
            model_to_use = self._get_model_with_profile(model, inference_profile_arn)

            # Common parameters for invoke_model
            invoke_params = {
                "modelId": model_to_use,
            }

            if model.startswith("anthropic.claude"):
                # Format for Claude models
                system_message, formatted_messages = self._format_messages_for_claude(messages)
                
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens or 2000,
                    "messages": formatted_messages
                }
                
                if system:
                    request_body["system"] = system
                elif system_message:
                    request_body["system"] = system_message

                # Use the Claude-specific streaming handler
                async for chunk in self._stream_claude_response(model, request_body, inference_profile_arn):
                    yield chunk

            elif model.startswith("amazon.titan"):
                # Format for Titan models
                request_body = {
                    "inputText": self._format_messages_for_titan(messages),
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens or 2000,
                        "temperature": 0.7,
                        "topP": 0.9,
                        "stopSequences": []
                    }
                }

                # Use the Titan-specific streaming handler
                async for chunk in self._stream_titan_response(model, request_body, inference_profile_arn):
                    yield chunk

            elif model.startswith("meta.llama"):
                # Format for Llama models
                request_body = {
                    "prompt": self._format_messages_for_llama(messages),
                    "max_gen_len": max_tokens or 512,
                    "temperature": 0.7,
                    "top_p": 0.9
                }

                # Use the Llama-specific streaming handler
                async for chunk in self._stream_llama_response(model, request_body, inference_profile_arn):
                    yield chunk

            elif model.startswith("mistral"):
                # Format for Mistral models
                request_body = {
                    "prompt": self._format_messages_for_mistral(messages),
                    "max_tokens": max_tokens or 2000,
                    "temperature": 0.7,
                    "top_p": 0.9
                }

                # Use the Mistral-specific streaming handler
                async for chunk in self._stream_mistral_response(model, request_body, inference_profile_arn):
                    yield chunk

            else:
                raise ValueError(f"Unsupported model for streaming: {model}")

        except Exception as e:
            print(f"Error generating streaming chat completion: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise
# Create a singleton instance
bedrock_client = BedrockClient()
