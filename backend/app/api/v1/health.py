"""Health check endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text

from app.core.deps import DbSession
from app.vector_store.qdrant_client import QdrantVectorStore

router = APIRouter()


class HealthStatus(BaseModel):
    """Health check response."""

    status: str
    database: str
    vector_store: str
    version: str = "1.0.0"


@router.get("/health", response_model=HealthStatus)
async def health_check(
    db: DbSession,
) -> HealthStatus:
    """
    Check service health.

    Returns status of all critical components:
    - Database connection
    - Vector store connection
    """
    # Check database
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    # Check vector store
    vector_status = "healthy"
    try:
        vector_store = QdrantVectorStore()
        is_healthy = await vector_store.health_check()
        if not is_healthy:
            vector_status = "unhealthy"
    except Exception:
        vector_status = "unhealthy"

    # Overall status
    overall = "healthy" if db_status == "healthy" and vector_status == "healthy" else "degraded"

    return HealthStatus(
        status=overall,
        database=db_status,
        vector_store=vector_status,
    )


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    """Kubernetes liveness probe - is the service running?"""
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness(db: DbSession) -> dict[str, str]:
    """Kubernetes readiness probe - is the service ready to receive traffic?"""
    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        return {"status": "not_ready", "reason": "database_unavailable"}

    return {"status": "ready"}
