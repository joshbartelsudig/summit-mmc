from fastapi import APIRouter

from app.api.routes.models import router as models_router
from app.api.routes.chat import router as chat_router

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(models_router, tags=["models"])
api_router.include_router(chat_router, tags=["chat"])
