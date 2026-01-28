"""Retrieval service with hybrid search and RBAC enforcement."""

from typing import Any

from app.core.config import settings
from app.core.logging import SecurityLogger, get_logger
from app.core.rbac import RBACService
from app.schemas.document import RetrievalResult
from app.schemas.user import UserContext
from app.services.ingestion.embedder import EmbeddingGenerator
from app.services.retrieval.bm25 import BM25Index
from app.services.retrieval.reranker import LocalReranker, reciprocal_rank_fusion
from app.vector_store.qdrant_client import QdrantVectorStore

logger = get_logger(__name__)
security_logger = SecurityLogger()


class RetrievalService:
    """
    Hybrid retrieval service with RBAC enforcement.

    Two-stage retrieval pipeline:
    1. Build RBAC filter for user (SECURITY ENFORCEMENT)
    2. Vector search (top-20) with RBAC filter
    3. BM25 search (top-20) filtered to RBAC-allowed documents
    4. Reciprocal Rank Fusion (RRF) to combine results
    5. Rerank (top-5) with local cross-encoder
    6. Log document access for audit

    CRITICAL: RBAC filter is applied BEFORE retrieval, ensuring
    unauthorized documents never enter the pipeline.
    """

    def __init__(
        self,
        vector_store: QdrantVectorStore | None = None,
        embedder: EmbeddingGenerator | None = None,
        reranker: LocalReranker | None = None,
        bm25_index: BM25Index | None = None,
        rbac_service: RBACService | None = None,
    ) -> None:
        """
        Initialize retrieval service.

        Args:
            vector_store: Qdrant client for vector search
            embedder: Embedding generator for query embedding
            reranker: Local cross-encoder reranker
            bm25_index: BM25 sparse retrieval index
            rbac_service: RBAC filter builder service
        """
        self.vector_store = vector_store or QdrantVectorStore()
        self.embedder = embedder or EmbeddingGenerator()
        self.reranker = reranker or LocalReranker()
        self.bm25_index = bm25_index or BM25Index()
        self.rbac_service = rbac_service or RBACService()

        self._bm25_initialized = False

        logger.info("retrieval_service_initialized")

    async def ensure_bm25_index(self) -> None:
        """Build BM25 index from Qdrant if not already built."""
        if self._bm25_initialized:
            return

        try:
            count = await self.bm25_index.build_from_qdrant(self.vector_store)
            self._bm25_initialized = True
            logger.info("bm25_index_ready", document_count=count)
        except Exception as e:
            logger.warning(
                "bm25_index_build_failed",
                error=str(e),
                message="Falling back to vector-only search",
            )

    async def retrieve(
        self,
        query: str,
        user_context: UserContext,
        top_k: int = 5,
        initial_limit: int = 20,
        trace_id: str | None = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve documents using hybrid search with RBAC.

        Args:
            query: Search query
            user_context: User context for RBAC filtering
            top_k: Final number of results after reranking
            initial_limit: Number of candidates from each retrieval method
            trace_id: Request trace ID for logging

        Returns:
            List of retrieval results with documents and scores
        """
        logger.info(
            "retrieval_started",
            query_length=len(query),
            user_id=user_context.user_id,
            role=user_context.role,
            trace_id=trace_id,
        )

        # 1. Build RBAC filter (SECURITY CRITICAL)
        rbac_filter = self.rbac_service.get_filter_for_user(user_context)

        # 2. Generate query embedding
        query_embedding = await self.embedder.embed_query(query)

        # 3. Vector search with RBAC filter
        vector_results = await self.vector_store.search_with_rbac(
            query_vector=query_embedding,
            rbac_filter=rbac_filter,
            limit=initial_limit,
        )

        logger.debug(
            "vector_search_complete",
            num_results=len(vector_results),
            trace_id=trace_id,
        )

        # 4. Extract allowed document IDs for BM25 filtering
        # This ensures BM25 only returns documents the user can access
        allowed_doc_ids = {
            r.payload.get("document_id", "") for r in vector_results if r.payload
        }

        # Convert vector results to common format
        vector_docs = [
            {
                "id": str(r.id),
                "document_id": r.payload.get("document_id", "") if r.payload else "",
                "text": r.payload.get("text", "") if r.payload else "",
                "title": r.payload.get("title", "") if r.payload else "",
                "payload": r.payload or {},
                "vector_score": r.score,
            }
            for r in vector_results
        ]

        # 5. BM25 search (filtered to RBAC-allowed documents)
        bm25_results = []
        if self._bm25_initialized and allowed_doc_ids:
            bm25_raw = self.bm25_index.search(
                query=query,
                allowed_document_ids=allowed_doc_ids,
                limit=initial_limit,
            )
            bm25_results = [(doc, score) for doc, score in bm25_raw]

            logger.debug(
                "bm25_search_complete",
                num_results=len(bm25_results),
                trace_id=trace_id,
            )

        # 6. Combine with Reciprocal Rank Fusion
        vector_ranked = [(doc, doc["vector_score"]) for doc in vector_docs]

        if bm25_results:
            fused_results = reciprocal_rank_fusion(vector_ranked, bm25_results)
        else:
            # Fall back to vector-only if BM25 not available
            fused_results = vector_ranked

        logger.debug(
            "fusion_complete",
            num_fused=len(fused_results),
            trace_id=trace_id,
        )

        # 7. Extract documents for reranking
        candidates = [doc for doc, _score in fused_results[:initial_limit]]

        # 8. Rerank with cross-encoder
        reranked = self.reranker.rerank(
            query=query,
            documents=candidates,
            top_k=top_k,
        )

        # 9. Convert to RetrievalResult format
        results = []
        for doc, score in reranked:
            payload = doc.get("payload", {})

            result = RetrievalResult(
                document_id=doc.get("document_id", ""),
                chunk_id=doc.get("id", ""),
                title=payload.get("title", ""),
                text=doc.get("text", ""),
                doc_type=payload.get("doc_type", ""),
                department=payload.get("department", ""),
                access_level=payload.get("access_level", ""),
                score=float(score),
                vector_score=doc.get("vector_score", 0.0),
                chunk_index=payload.get("chunk_index", 0),
                chunk_count=payload.get("chunk_count", 1),
                citation=self._build_citation(payload),
            )
            results.append(result)

        # 10. Log document access for audit
        await self._log_document_access(
            user_context=user_context,
            results=results,
            trace_id=trace_id,
        )

        logger.info(
            "retrieval_complete",
            query_length=len(query),
            num_results=len(results),
            user_id=user_context.user_id,
            trace_id=trace_id,
        )

        return results

    def _build_citation(self, payload: dict[str, Any]) -> str:
        """Build citation string for document."""
        title = payload.get("title", "Unknown")
        doc_type = payload.get("doc_type", "document")
        department = payload.get("department", "")

        if department:
            return f"[{title}] ({doc_type}, {department})"
        return f"[{title}] ({doc_type})"

    async def _log_document_access(
        self,
        user_context: UserContext,
        results: list[RetrievalResult],
        trace_id: str | None,
    ) -> None:
        """
        Log document access for audit compliance.

        Special logging for confidential/restricted documents.
        """
        for result in results:
            # Log confidential access
            if result.access_level in ("confidential", "restricted"):
                security_logger.log_confidential_access(
                    user_id=user_context.user_id,
                    document_id=result.document_id,
                    action="retrieve",
                    trace_id=trace_id,
                )

    async def retrieve_simple(
        self,
        query: str,
        user_context: UserContext,
        limit: int = 5,
    ) -> list[RetrievalResult]:
        """
        Simple vector-only retrieval (no BM25 or reranking).

        Useful for quick searches or when latency is critical.

        Args:
            query: Search query
            user_context: User context for RBAC filtering
            limit: Number of results

        Returns:
            List of retrieval results
        """
        # Build RBAC filter
        rbac_filter = self.rbac_service.get_filter_for_user(user_context)

        # Generate query embedding
        query_embedding = await self.embedder.embed_query(query)

        # Vector search with RBAC
        results = await self.vector_store.search_with_rbac(
            query_vector=query_embedding,
            rbac_filter=rbac_filter,
            limit=limit,
        )

        # Convert to RetrievalResult
        return [
            RetrievalResult(
                document_id=r.payload.get("document_id", "") if r.payload else "",
                chunk_id=str(r.id),
                title=r.payload.get("title", "") if r.payload else "",
                text=r.payload.get("text", "") if r.payload else "",
                doc_type=r.payload.get("doc_type", "") if r.payload else "",
                department=r.payload.get("department", "") if r.payload else "",
                access_level=r.payload.get("access_level", "") if r.payload else "",
                score=r.score,
                chunk_index=r.payload.get("chunk_index", 0) if r.payload else 0,
                chunk_count=r.payload.get("chunk_count", 1) if r.payload else 1,
                citation=self._build_citation(r.payload or {}),
            )
            for r in results
        ]

    async def get_document_by_id(
        self,
        document_id: str,
        user_context: UserContext,
    ) -> list[RetrievalResult] | None:
        """
        Get all chunks of a specific document (with RBAC check).

        Args:
            document_id: Document ID to retrieve
            user_context: User context for RBAC filtering

        Returns:
            List of chunks if user has access, None otherwise
        """
        # Build RBAC filter
        rbac_filter = self.rbac_service.get_filter_for_user(user_context)

        # Search by document ID with RBAC filter
        results = await self.vector_store.get_by_document_id(
            document_id=document_id,
            rbac_filter=rbac_filter,
        )

        if not results:
            return None

        # Convert to RetrievalResult
        return [
            RetrievalResult(
                document_id=r.payload.get("document_id", "") if r.payload else "",
                chunk_id=str(r.id),
                title=r.payload.get("title", "") if r.payload else "",
                text=r.payload.get("text", "") if r.payload else "",
                doc_type=r.payload.get("doc_type", "") if r.payload else "",
                department=r.payload.get("department", "") if r.payload else "",
                access_level=r.payload.get("access_level", "") if r.payload else "",
                score=1.0,  # Direct fetch, no relevance score
                chunk_index=r.payload.get("chunk_index", 0) if r.payload else 0,
                chunk_count=r.payload.get("chunk_count", 1) if r.payload else 1,
                citation=self._build_citation(r.payload or {}),
            )
            for r in results
        ]
