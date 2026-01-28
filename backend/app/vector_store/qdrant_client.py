"""
Qdrant Vector Store Client.

SECURITY NOTE: All searches MUST use RBAC filters from RBACFilterBuilder.
Never call search methods without a filter - this would bypass access control.
"""

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    ScoredPoint,
    VectorParams,
)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class QdrantVectorStore:
    """
    Qdrant client wrapper with RBAC-aware search.

    CRITICAL SECURITY REQUIREMENT:
    All search operations MUST include an RBAC filter from RBACFilterBuilder.
    The search_with_rbac() method is the ONLY way to search - it enforces
    that a filter is always provided.

    Usage:
        store = QdrantVectorStore()
        await store.create_collection()

        # CORRECT - RBAC enforced
        rbac_filter = rbac_builder.build_filter(user_context)
        results = await store.search_with_rbac(embedding, rbac_filter)

        # WRONG - Never do this
        # results = client.search(...)  # Bypasses RBAC!
    """

    def __init__(
        self,
        url: str | None = None,
        collection_name: str | None = None,
    ) -> None:
        """
        Initialize Qdrant client.

        Args:
            url: Qdrant server URL (defaults to settings.qdrant_url)
            collection_name: Collection name (defaults to settings.qdrant_collection)
        """
        self.url = url or settings.qdrant_url
        self.collection_name = collection_name or settings.qdrant_collection
        self.client = QdrantClient(url=self.url)

        logger.info(
            "qdrant_client_initialized",
            url=self.url,
            collection=self.collection_name,
        )

    async def create_collection(
        self,
        vector_size: int | None = None,
        recreate: bool = False,
    ) -> None:
        """
        Create collection with proper indexes for RBAC filtering.

        Args:
            vector_size: Embedding dimensions (defaults to settings.embedding_dimensions)
            recreate: If True, delete and recreate collection
        """
        vector_size = vector_size or settings.embedding_dimensions

        # Check if collection exists
        collections = self.client.get_collections()
        exists = any(c.name == self.collection_name for c in collections.collections)

        if exists and not recreate:
            logger.info("collection_exists", collection=self.collection_name)
            return

        if exists and recreate:
            self.client.delete_collection(self.collection_name)
            logger.info("collection_deleted", collection=self.collection_name)

        # Create collection
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

        # Create payload indexes for RBAC filtering
        # These indexes enable fast filtering at query time
        indexed_fields = [
            # Core document fields
            ("document_id", PayloadSchemaType.KEYWORD),
            ("doc_type", PayloadSchemaType.KEYWORD),
            ("access_level", PayloadSchemaType.KEYWORD),
            ("department", PayloadSchemaType.KEYWORD),
            ("status", PayloadSchemaType.KEYWORD),
            ("owner_id", PayloadSchemaType.KEYWORD),
            # RBAC fields
            ("allowed_roles", PayloadSchemaType.KEYWORD),
            ("allowed_departments", PayloadSchemaType.KEYWORD),
            ("granted_users", PayloadSchemaType.KEYWORD),
            ("denied_users", PayloadSchemaType.KEYWORD),
            # Temporal fields
            ("available_from", PayloadSchemaType.DATETIME),
            ("available_until", PayloadSchemaType.DATETIME),
            # Manager scope fields
            ("manager_scope.direct_reports_only", PayloadSchemaType.BOOL),
            ("manager_scope.employee_id", PayloadSchemaType.KEYWORD),
        ]

        for field_name, field_type in indexed_fields:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_type,
                )
            except Exception as e:
                # Some indexes might fail if field doesn't exist yet
                logger.warning(
                    "index_creation_warning",
                    field=field_name,
                    error=str(e),
                )

        logger.info(
            "collection_created",
            collection=self.collection_name,
            vector_size=vector_size,
            indexed_fields=len(indexed_fields),
        )

    async def search_with_rbac(
        self,
        query_vector: list[float],
        rbac_filter: Filter,
        limit: int = 20,
        score_threshold: float | None = None,
    ) -> list[ScoredPoint]:
        """
        RBAC-filtered vector search.

        CRITICAL: The rbac_filter parameter MUST come from RBACFilterBuilder.
        This is the security enforcement point where unauthorized documents
        are excluded from search results.

        Args:
            query_vector: Query embedding vector
            rbac_filter: RBAC filter from RBACFilterBuilder (REQUIRED)
            limit: Maximum number of results
            score_threshold: Minimum similarity score (optional)

        Returns:
            List of scored points matching the filter
        """
        if rbac_filter is None:
            raise ValueError(
                "SECURITY ERROR: rbac_filter is required. "
                "Use RBACFilterBuilder to create a filter."
            )

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=rbac_filter,  # RBAC enforced HERE
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
        )

        logger.info(
            "rbac_filtered_search",
            result_count=len(results),
            limit=limit,
            has_filter=True,
        )

        return results

    async def upsert_points(
        self,
        points: list[PointStruct],
    ) -> None:
        """
        Insert or update document points.

        Args:
            points: List of points to upsert
        """
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        logger.info("points_upserted", count=len(points))

    async def upsert_document_chunk(
        self,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        """
        Insert or update a single document chunk.

        Args:
            point_id: Unique point identifier
            vector: Embedding vector
            payload: Document metadata (must include RBAC fields)
        """
        point = PointStruct(
            id=point_id,
            vector=vector,
            payload=payload,
        )

        await self.upsert_points([point])

    async def delete_document(self, document_id: str) -> None:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID to delete
        """
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            ),
        )

        logger.info("document_deleted", document_id=document_id)

    async def get_by_document_id(
        self,
        document_id: str,
        rbac_filter: Filter,
        limit: int = 100,
    ) -> list[ScoredPoint]:
        """
        Get all chunks for a document with RBAC filtering.

        Args:
            document_id: Document ID to retrieve
            rbac_filter: RBAC filter from RBACFilterBuilder (REQUIRED)
            limit: Maximum chunks to return

        Returns:
            List of points for the document (empty if no access)
        """
        if rbac_filter is None:
            raise ValueError(
                "SECURITY ERROR: rbac_filter is required. "
                "Use RBACFilterBuilder to create a filter."
            )

        # Combine document ID filter with RBAC filter
        doc_filter = Filter(
            must=[
                FieldCondition(key="document_id", match=MatchValue(value=document_id)),
                rbac_filter,  # RBAC enforced HERE
            ]
        )

        results, _offset = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=doc_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        logger.debug(
            "get_by_document_id",
            document_id=document_id,
            chunks_found=len(results),
        )

        return results

    async def get_collection_info(self) -> dict[str, Any]:
        """Get collection statistics and info."""
        info = self.client.get_collection(self.collection_name)
        return {
            "name": self.collection_name,
            "points_count": info.points_count,
            "vectors_count": info.vectors_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "status": info.status.value,
        }

    async def health_check(self) -> bool:
        """Check if Qdrant is healthy and collection exists."""
        try:
            collections = self.client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)
            return exists
        except Exception as e:
            logger.error("qdrant_health_check_failed", error=str(e))
            return False
