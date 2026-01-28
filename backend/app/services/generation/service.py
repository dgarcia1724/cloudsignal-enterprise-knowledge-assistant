"""RAG generation service."""

from collections.abc import AsyncGenerator
from typing import Any

from app.core.logging import SecurityLogger, get_logger
from app.schemas.chat import ChatMessage, ChatResponse, StreamChunk
from app.schemas.document import RetrievalResult
from app.schemas.user import UserContext
from app.services.generation.llm_client import LLMClient, build_rag_prompt
from app.services.retrieval.service import RetrievalService

logger = get_logger(__name__)
security_logger = SecurityLogger()


class GenerationService:
    """
    RAG generation service.

    Orchestrates the full RAG pipeline:
    1. Retrieve relevant documents (with RBAC)
    2. Build prompt with context
    3. Generate response with LLM
    4. Return with citations
    """

    def __init__(
        self,
        retrieval_service: RetrievalService | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        """
        Initialize generation service.

        Args:
            retrieval_service: Retrieval service for document search
            llm_client: LLM client for generation
        """
        self.retrieval_service = retrieval_service or RetrievalService()
        self.llm_client = llm_client or LLMClient()

        logger.info("generation_service_initialized")

    async def generate_response(
        self,
        query: str,
        user_context: UserContext,
        trace_id: str | None = None,
    ) -> ChatResponse:
        """
        Generate a RAG response (non-streaming).

        Args:
            query: User's question
            user_context: User context for RBAC
            trace_id: Request trace ID

        Returns:
            Chat response with answer and citations
        """
        logger.info(
            "generation_started",
            query_length=len(query),
            user_id=user_context.user_id,
            trace_id=trace_id,
        )

        # 1. Retrieve relevant documents (RBAC enforced)
        results = await self.retrieval_service.retrieve(
            query=query,
            user_context=user_context,
            top_k=5,
            trace_id=trace_id,
        )

        if not results:
            logger.warning(
                "no_documents_retrieved",
                query=query,
                user_id=user_context.user_id,
                trace_id=trace_id,
            )
            return ChatResponse(
                message=ChatMessage(
                    role="assistant",
                    content="I don't have any relevant documents to answer that question. "
                    "Please try rephrasing your question or ask about a different topic.",
                ),
                sources=[],
                trace_id=trace_id,
            )

        # 2. Build prompt with context
        context_docs = self._results_to_context(results)
        messages = build_rag_prompt(query, context_docs)

        # 3. Generate response
        response_text = await self.llm_client.generate(messages)

        # 4. Extract citations
        citations = self._extract_citations(results)

        logger.info(
            "generation_complete",
            query_length=len(query),
            response_length=len(response_text),
            num_sources=len(citations),
            trace_id=trace_id,
        )

        return ChatResponse(
            message=ChatMessage(role="assistant", content=response_text),
            sources=citations,
            trace_id=trace_id,
        )

    async def generate_stream(
        self,
        query: str,
        user_context: UserContext,
        trace_id: str | None = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Generate a streaming RAG response.

        Args:
            query: User's question
            user_context: User context for RBAC
            trace_id: Request trace ID

        Yields:
            Stream chunks with content and metadata
        """
        logger.info(
            "stream_generation_started",
            query_length=len(query),
            user_id=user_context.user_id,
            trace_id=trace_id,
        )

        # 1. Retrieve relevant documents (RBAC enforced)
        results = await self.retrieval_service.retrieve(
            query=query,
            user_context=user_context,
            top_k=5,
            trace_id=trace_id,
        )

        if not results:
            yield StreamChunk(
                type="content",
                content="I don't have any relevant documents to answer that question.",
            )
            yield StreamChunk(type="done", content="")
            return

        # 2. Build prompt with context
        context_docs = self._results_to_context(results)
        messages = build_rag_prompt(query, context_docs)

        # 3. Send sources first
        citations = self._extract_citations(results)
        yield StreamChunk(type="sources", sources=citations)

        # 4. Stream response
        async for chunk in self.llm_client.generate_stream(messages):
            yield StreamChunk(type="content", content=chunk)

        # 5. Signal completion
        yield StreamChunk(type="done", content="")

        logger.info(
            "stream_generation_complete",
            query_length=len(query),
            num_sources=len(citations),
            trace_id=trace_id,
        )

    def _results_to_context(
        self,
        results: list[RetrievalResult],
    ) -> list[dict[str, Any]]:
        """Convert retrieval results to context documents."""
        return [
            {
                "title": r.title,
                "text": r.text,
                "doc_type": r.doc_type,
                "department": r.department,
                "document_id": r.document_id,
            }
            for r in results
        ]

    def _extract_citations(
        self,
        results: list[RetrievalResult],
    ) -> list[dict[str, Any]]:
        """Extract citation information from results."""
        # Deduplicate by document_id (multiple chunks from same doc)
        seen_docs = set()
        citations = []

        for r in results:
            if r.document_id in seen_docs:
                continue
            seen_docs.add(r.document_id)

            citations.append(
                {
                    "document_id": r.document_id,
                    "title": r.title,
                    "doc_type": r.doc_type,
                    "department": r.department,
                    "citation": r.citation,
                }
            )

        return citations

    async def check_prompt_injection(
        self,
        query: str,
        user_context: UserContext,
        trace_id: str | None = None,
    ) -> bool:
        """
        Check if query contains potential prompt injection.

        Simple heuristic-based detection. Returns True if suspicious.

        Args:
            query: User's query
            user_context: User context for logging
            trace_id: Request trace ID

        Returns:
            True if query is suspicious, False otherwise
        """
        # Common injection patterns
        injection_patterns = [
            "ignore previous instructions",
            "ignore all previous",
            "disregard previous",
            "forget your instructions",
            "new instructions:",
            "system prompt:",
            "you are now",
            "act as",
            "pretend to be",
            "reveal your prompt",
            "show your instructions",
            "what are your instructions",
            "ignore the rules",
            "bypass",
        ]

        query_lower = query.lower()

        for pattern in injection_patterns:
            if pattern in query_lower:
                security_logger.log_prompt_injection(
                    user_id=user_context.user_id,
                    query=query,
                    detected_pattern=pattern,
                    trace_id=trace_id,
                )
                return True

        return False
