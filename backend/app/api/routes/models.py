from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.models.schemas import ModelsResponse, Model
from app.services.model_router import model_router

router = APIRouter()

@router.get("/models", response_model=ModelsResponse)
async def list_models(refresh: bool = False):
    """
    List available models
    
    Args:
        refresh (bool): Whether to force a refresh of the model list
        
    Returns:
        ModelsResponse: List of available models
    """
    try:
        # Clear any cached models in the clients if refresh is requested
        if refresh and hasattr(model_router.bedrock_client, '_cached_models'):
            delattr(model_router.bedrock_client, '_cached_models')
        
        # Get list of models, forcing a refresh if requested
        models = model_router.list_all_models(use_cache=not refresh)
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing models: {str(e)}")
