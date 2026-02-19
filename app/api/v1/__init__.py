"""
API v1 module
"""
from fastapi import APIRouter
from app.api.v1.endpoints import users, llm, history, hyperparameters, admin, auth

# Create the main API router for v1
api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(users.router)
api_router.include_router(llm.router)
api_router.include_router(history.router)
api_router.include_router(hyperparameters.router)
api_router.include_router(admin.router)
api_router.include_router(auth.router)

__all__ = ["api_router"]
