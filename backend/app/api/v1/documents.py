"""Document endpoints for viewing accessible documents."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import CurrentUser, TraceId
from app.core.logging import get_logger
from app.schemas.document import DocumentList, RetrievalResult
from app.services.retrieval.service import RetrievalService

router = APIRouter()
logger = get_logger(__name__)


def get_retrieval_service() -> RetrievalService:
    """Dependency to get retrieval service."""
    return RetrievalService()


@router.get("/documents", response_model=DocumentList)
async def list_documents(
    user: CurrentUser,
    trace_id: TraceId,
    service: Annotated[RetrievalService, Depends(get_retrieval_service)],
    search: str | None = Query(None, description="Optional search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum documents to return"),
) -> DocumentList:
    """
    List documents accessible to the current user.

    Returns documents filtered by the user's RBAC permissions.
    Optionally search within accessible documents.

    Args:
        search: Optional search query
        limit: Maximum number of documents to return

    Returns:
        List of accessible documents
    """
    logger.info(
        "list_documents_request",
        user_id=user.user_id,
        role=user.role,
        search=search,
        limit=limit,
        trace_id=trace_id,
    )

    if search:
        # Search within accessible documents
        results = await service.retrieve_simple(
            query=search,
            user_context=user,
            limit=limit,
        )
    else:
        # List recent/popular documents (simple vector search with generic query)
        results = await service.retrieve_simple(
            query="company documents policies procedures",
            user_context=user,
            limit=limit,
        )

    # Deduplicate by document_id (multiple chunks)
    seen_docs: set[str] = set()
    unique_results: list[RetrievalResult] = []
    for r in results:
        if r.document_id not in seen_docs:
            seen_docs.add(r.document_id)
            unique_results.append(r)

    return DocumentList(
        documents=unique_results,
        total=len(unique_results),
        trace_id=trace_id,
    )


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    user: CurrentUser,
    trace_id: TraceId,
    service: Annotated[RetrievalService, Depends(get_retrieval_service)],
) -> dict[str, Any]:
    """
    Get a specific document by ID.

    Returns the document if the user has access, 404 otherwise.
    Note: This doesn't reveal whether the document exists if access is denied.

    Args:
        document_id: Document identifier

    Returns:
        Document content and metadata
    """
    logger.info(
        "get_document_request",
        user_id=user.user_id,
        role=user.role,
        document_id=document_id,
        trace_id=trace_id,
    )

    results = await service.get_document_by_id(
        document_id=document_id,
        user_context=user,
    )

    if not results:
        # Don't reveal whether document exists - just say not found
        raise HTTPException(
            status_code=404,
            detail="Document not found or you don't have access",
        )

    # Combine chunks into full document
    chunks = sorted(results, key=lambda r: r.chunk_index)
    full_text = "\n\n".join(r.text for r in chunks)

    # Get metadata from first chunk
    first = chunks[0]

    return {
        "document_id": document_id,
        "title": first.title,
        "doc_type": first.doc_type,
        "department": first.department,
        "access_level": first.access_level,
        "content": full_text,
        "chunk_count": len(chunks),
        "trace_id": trace_id,
    }


@router.get("/documents/types/summary")
async def get_document_types(
    user: CurrentUser,
    trace_id: TraceId,
) -> dict[str, Any]:
    """
    Get summary of document types accessible to user.

    Returns the types of documents the user can access based on their role.
    This is useful for UI filtering and discovery.
    """
    # Map role to accessible document types
    role_doc_types = {
        "engineer": ["runbook", "design_doc", "postmortem", "api_doc", "architecture"],
        "sre": ["runbook", "incident_report", "monitoring_config", "design_doc", "postmortem"],
        "product_manager": ["product_roadmap", "feature_spec", "customer_feedback", "market_analysis"],
        "hr": ["policy", "benefits_guide", "salary_band", "performance_review", "onboarding"],
        "manager": ["team_doc", "performance_review", "policy", "budget"],
        "admin": ["all"],
    }

    accessible_types = role_doc_types.get(user.role, [])

    return {
        "role": user.role,
        "accessible_document_types": accessible_types,
        "trace_id": trace_id,
    }
