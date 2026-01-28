"""API v1 routes."""

from fastapi import APIRouter

from app.api.v1 import chat, documents, health

router = APIRouter(prefix="/api/v1")

router.include_router(health.router, tags=["health"])
router.include_router(chat.router, tags=["chat"])
router.include_router(documents.router, tags=["documents"])

__all__ = ["router"]
