from openai import AzureOpenAI
from typing import List, Dict, Any, Optional
import requests

from app.core.config import settings

class AzureOpenAIClient:
    """Client for Azure OpenAI API interactions"""
    
    def __init__(self):
        """Initialize the Azure OpenAI client"""
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )
        self.endpoint = settings.AZURE_OPENAI_ENDPOINT.rstrip('/')
        self.api_key = settings.AZURE_OPENAI_API_KEY
        self.api_version = settings.AZURE_OPENAI_API_VERSION
        
        # Parse deployed models from environment variable
        self.deployed_models = [model.strip() for model in settings.AZURE_OPENAI_DEPLOYED_MODELS.split(",") if model.strip()]
        
        # Azure Resource Manager configuration
        self.subscription_id = settings.AZURE_SUBSCRIPTION_ID
        self.resource_group = settings.AZURE_RESOURCE_GROUP
        self.resource_name = settings.AZURE_RESOURCE_NAME
        self.tenant_id = settings.AZURE_TENANT_ID
        self.client_id = settings.AZURE_CLIENT_ID
        self.client_secret = settings.AZURE_CLIENT_SECRET
        
        # Check if we have all the required ARM credentials
        self.can_use_arm_api = all([
            self.subscription_id,
            self.resource_group,
            self.resource_name,
            self.tenant_id,
            self.client_id,
            self.client_secret
        ])
    
    def list_deployments(self) -> List[Dict[str, Any]]:
        """
        List deployed models from Azure OpenAI
        
        Returns:
            List[Dict[str, Any]]: List of deployed models
        """
        # Try to get deployments using ARM API if credentials are available
        if self.can_use_arm_api:
            try:
                arm_deployments = self._get_deployments_from_arm()
                if arm_deployments:
                    return arm_deployments
            except Exception as e:
                print(f"Error getting deployments from ARM API: {e}")
        
        # Fall back to using the deployed models from environment variable
        try:
            # Model name mapping
            model_names = {
                "gpt-35-turbo": "GPT-3.5 Turbo",
                "gpt-4": "GPT-4",
                "gpt-4-turbo": "GPT-4 Turbo",
                "gpt-4-vision": "GPT-4 Vision",
                "text-embedding-ada-002": "Text Embedding Ada 002"
            }
            
            # Use the deployed models from environment variable
            if self.deployed_models:
                return [
                    {
                        "id": model_id,
                        "provider": "azure",
                        "name": model_names.get(model_id, model_id)
                    }
                    for model_id in self.deployed_models
                ]
            else:
                print("No deployed models specified in environment variable, returning default models")
                return self._get_default_models()
        except Exception as e:
            print(f"Error listing Azure OpenAI deployments: {e}")
            return self._get_default_models()
    
    def _get_default_models(self) -> List[Dict[str, Any]]:
        """
        Get default models if API call fails
        
        Returns:
            List[Dict[str, Any]]: List of default models
        """
        return [
            {"id": "gpt-35-turbo", "provider": "azure", "name": "GPT-3.5 Turbo"},
            {"id": "gpt-4", "provider": "azure", "name": "GPT-4"}
        ]
    
    def _get_deployments_from_arm(self) -> List[Dict[str, Any]]:
        """
        Get deployments from Azure Resource Manager API
        
        Returns:
            List[Dict[str, Any]]: List of deployments
        """
        # Get Azure AD token
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/token"
        token_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "resource": "https://management.azure.com/"
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]
        
        # Get deployments from ARM API
        deployments_url = f"https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.CognitiveServices/accounts/{self.resource_name}/deployments?api-version=2023-05-01"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        deployments_response = requests.get(deployments_url, headers=headers)
        deployments_response.raise_for_status()
        deployments_data = deployments_response.json()
        
        # Format deployments
        model_names = {
            "gpt-35-turbo": "GPT-3.5 Turbo",
            "gpt-4": "GPT-4",
            "gpt-4-turbo": "GPT-4 Turbo",
            "gpt-4-vision": "GPT-4 Vision",
            "text-embedding-ada-002": "Text Embedding Ada 002"
        }
        
        formatted_deployments = []
        for deployment in deployments_data.get("value", []):
            model_id = deployment["name"]
            formatted_deployments.append({
                "id": model_id,
                "provider": "azure",
                "name": model_names.get(model_id, model_id)
            })
        
        return formatted_deployments
    
    async def generate_chat_completion(self, messages, model):
        """
        Generate chat completion using Azure OpenAI
        
        Args:
            messages (List[Dict]): List of messages
            model (str): Model ID
            
        Returns:
            Dict: Chat completion response
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": msg.role, "content": msg.content} for msg in messages],
            )
            
            # Convert the response object to a dictionary
            response_dict = {
                "id": response.id,
                "model": model,
                "choices": [
                    {
                        "message": {
                            "role": response.choices[0].message.role,
                            "content": response.choices[0].message.content
                        },
                        "finish_reason": response.choices[0].finish_reason
                    }
                ]
            }
            
            return response_dict
        except Exception as e:
            print(f"Error generating chat completion: {e}")
            raise

    async def generate_streaming_chat_completion(self, messages, model):
        """
        Generate streaming chat completion using Azure OpenAI
        
        Args:
            messages (List[Dict]): List of messages
            model (str): Model ID
            
        Returns:
            AsyncGenerator: Streaming chat completion response
        """
        try:
            # Create the completion with stream=True
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": msg.role, "content": msg.content} for msg in messages],
                stream=True
            )
            
            # Return a simple generator function that yields each chunk
            # The OpenAI response is already an iterator, so we just need to format each chunk
            for chunk in response:
                if hasattr(chunk.choices[0], 'delta'):
                    delta = chunk.choices[0].delta
                    yield {
                        "id": chunk.id,
                        "model": model,
                        "choices": [
                            {
                                "delta": {
                                    "role": delta.role if hasattr(delta, 'role') else None,
                                    "content": delta.content if hasattr(delta, 'content') else ""
                                },
                                "finish_reason": chunk.choices[0].finish_reason
                            }
                        ]
                    }
        except Exception as e:
            print(f"Error generating streaming chat completion: {e}")
            raise

# Create a singleton instance
azure_client = AzureOpenAIClient()
