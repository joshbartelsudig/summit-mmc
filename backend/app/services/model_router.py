from typing import List, Dict, Any, Union, AsyncGenerator, Optional

from app.models.schemas import ChatMessage
from app.services.azure_openai import azure_client
from app.services.bedrock import bedrock_client

class ModelRouter:
    """Router for model selection and API calls"""
    
    def __init__(self):
        """Initialize the model router"""
        self.azure_client = azure_client
        self.bedrock_client = bedrock_client
    
    def list_all_models(self, use_cache=True) -> List[Dict[str, Any]]:
        """
        List all available models from all providers
        
        Args:
            use_cache (bool): Whether to use cached models if available
            
        Returns:
            List[Dict[str, Any]]: List of all available models
        """
        azure_models = self.azure_client.list_deployments()
        bedrock_models = self.bedrock_client.list_models(use_cache=use_cache)
        
        return azure_models + bedrock_models
    
    async def route_chat_completion(
        self, 
        messages: List[ChatMessage], 
        model: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        inference_profile_arn: str = None
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """
        Route chat completion request to the appropriate provider
        
        Args:
            messages (List[ChatMessage]): List of messages
            model (str): Model ID
            system (str, optional): System message for models that support it (e.g. Anthropic)
            max_tokens (int, optional): Maximum number of tokens to generate
            stream (bool): Whether to stream the response
            inference_profile_arn (str, optional): ARN of the inference profile to use for Bedrock models
            
        Returns:
            Union[Dict, AsyncGenerator]: Chat completion response
        """
        # Determine the provider based on the model ID
        if model.startswith(("gpt-", "o1", "azure-")):
            # Azure OpenAI
            if stream:
                # For Azure OpenAI streaming, we need to convert the regular generator to an async generator
                generator = self.azure_client.generate_streaming_chat_completion(messages, model)
                
                # Convert to async generator
                async def async_generator():
                    for chunk in generator:
                        yield chunk
                
                return async_generator()
            else:
                return await self.azure_client.generate_chat_completion(messages, model)
        elif model.startswith(("anthropic.", "amazon.", "meta.", "mistral.")):
            # Amazon Bedrock
            if stream:
                return self.bedrock_client.generate_chat_completion_stream(
                    messages=messages,
                    model=model,
                    system=system,
                    max_tokens=max_tokens,
                    inference_profile_arn=inference_profile_arn
                )
            else:
                return await self.bedrock_client.generate_chat_completion(
                    messages=messages,
                    model=model,
                    system=system,
                    max_tokens=max_tokens,
                    inference_profile_arn=inference_profile_arn
                )
        else:
            # Default to Azure OpenAI if model provider can't be determined
            if stream:
                # For Azure OpenAI streaming, we need to convert the regular generator to an async generator
                generator = self.azure_client.generate_streaming_chat_completion(messages, model)
                
                # Convert to async generator
                async def async_generator():
                    for chunk in generator:
                        yield chunk
                
                return async_generator()
            else:
                return await self.azure_client.generate_chat_completion(messages, model)

# Create a singleton instance
model_router = ModelRouter()
