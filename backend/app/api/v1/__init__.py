"""API v1 router."""
from fastapi import APIRouter

from app.api.v1.endpoints import health, auth, chat, admin, documents

api_router = APIRouter()

# Include routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["authentication"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

# TODO: Add other routers as they are implemented
# api_router.include_router(user.router, prefix="/user", tags=["user"])
