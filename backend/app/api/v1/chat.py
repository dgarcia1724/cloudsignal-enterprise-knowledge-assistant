"""Chat endpoint for RAG queries."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.deps import CurrentUser, TraceId
from app.core.logging import get_logger
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.generation.service import GenerationService

router = APIRouter()
logger = get_logger(__name__)


def get_generation_service() -> GenerationService:
    """Dependency to get generation service."""
    return GenerationService()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: CurrentUser,
    trace_id: TraceId,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> ChatResponse:
    """
    Chat with the knowledge assistant.

    Performs RAG retrieval with RBAC filtering and returns a response
    with citations.

    Returns:
        ChatResponse with answer and source documents
    """
    logger.info(
        "chat_request",
        user_id=user.user_id,
        role=user.role,
        query_length=len(request.query),
        trace_id=trace_id,
    )

    # Check for prompt injection
    if await service.check_prompt_injection(request.query, user, trace_id):
        raise HTTPException(
            status_code=400,
            detail="Query contains potentially harmful content. Please rephrase your question.",
        )

    # Generate response
    response = await service.generate_response(
        query=request.query,
        user_context=user,
        trace_id=trace_id,
    )

    return response


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    user: CurrentUser,
    trace_id: TraceId,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> StreamingResponse:
    """
    Stream chat responses using Server-Sent Events (SSE).

    Returns a streaming response with chunks of the answer and metadata.
    Each chunk is a JSON object with a 'type' field:
    - 'sources': List of source documents
    - 'content': Partial response text
    - 'done': End of stream marker

    Example SSE events:
    ```
    data: {"type": "sources", "sources": [...]}
    data: {"type": "content", "content": "The "}
    data: {"type": "content", "content": "answer is..."}
    data: {"type": "done", "content": ""}
    ```
    """
    logger.info(
        "chat_stream_request",
        user_id=user.user_id,
        role=user.role,
        query_length=len(request.query),
        trace_id=trace_id,
    )

    # Check for prompt injection
    if await service.check_prompt_injection(request.query, user, trace_id):
        raise HTTPException(
            status_code=400,
            detail="Query contains potentially harmful content. Please rephrase your question.",
        )

    async def generate():
        """Generate SSE events."""
        async for chunk in service.generate_stream(
            query=request.query,
            user_context=user,
            trace_id=trace_id,
        ):
            # Format as SSE
            data = chunk.model_dump()
            yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Trace-ID": trace_id or "",
        },
    )
