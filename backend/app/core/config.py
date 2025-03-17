import os
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    """Application settings"""
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Multi-Model Chatbot API"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # In production, replace with specific origins
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    AZURE_OPENAI_DEPLOYED_MODELS: str = os.getenv("AZURE_OPENAI_DEPLOYED_MODELS", "gpt-35-turbo,gpt-4")
    
    # Azure Resource Manager Configuration (optional)
    AZURE_SUBSCRIPTION_ID: Optional[str] = os.getenv("AZURE_SUBSCRIPTION_ID")
    AZURE_RESOURCE_GROUP: Optional[str] = os.getenv("AZURE_RESOURCE_GROUP")
    AZURE_RESOURCE_NAME: Optional[str] = os.getenv("AZURE_RESOURCE_NAME")
    AZURE_TENANT_ID: Optional[str] = os.getenv("AZURE_TENANT_ID")
    AZURE_CLIENT_ID: Optional[str] = os.getenv("AZURE_CLIENT_ID")
    AZURE_CLIENT_SECRET: Optional[str] = os.getenv("AZURE_CLIENT_SECRET")
    
    # AWS Configuration for Bedrock
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    
    # AWS credentials
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields from environment

# Create global settings object
settings = Settings()
