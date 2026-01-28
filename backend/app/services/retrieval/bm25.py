"""BM25 sparse retrieval for hybrid search."""

import re
from typing import Any

from rank_bm25 import BM25Okapi

from app.core.logging import get_logger

logger = get_logger(__name__)


class BM25Retriever:
    """
    BM25 sparse retrieval using Okapi BM25.

    Used alongside vector search for hybrid retrieval.
    BM25 excels at exact keyword matching while vectors
    handle semantic similarity.
    """

    def __init__(self) -> None:
        """Initialize BM25 retriever."""
        self.documents: list[dict[str, Any]] = []
        self.bm25: BM25Okapi | None = None
        self._tokenized_corpus: list[list[str]] = []

        logger.info("bm25_retriever_initialized")

    def index_documents(self, documents: list[dict[str, Any]]) -> None:
        """
        Index documents for BM25 search.

        Args:
            documents: List of documents with 'text' field
        """
        self.documents = documents

        # Tokenize corpus
        self._tokenized_corpus = [
            self._tokenize(doc.get("text", "")) for doc in documents
        ]

        # Build BM25 index
        self.bm25 = BM25Okapi(self._tokenized_corpus)

        logger.info(
            "bm25_index_built",
            num_documents=len(documents),
        )

    def _tokenize(self, text: str) -> list[str]:
        """
        Tokenize text for BM25.

        Simple whitespace tokenization with lowercasing
        and basic punctuation removal.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        # Lowercase
        text = text.lower()

        # Remove punctuation except hyphens
        text = re.sub(r"[^\w\s-]", " ", text)

        # Split on whitespace
        tokens = text.split()

        # Remove empty tokens
        tokens = [t.strip() for t in tokens if t.strip()]

        return tokens

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[tuple[dict[str, Any], float]]:
        """
        Search documents using BM25.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            List of (document, score) tuples sorted by score descending
        """
        if not self.bm25 or not self.documents:
            logger.warning("bm25_search_no_index")
            return []

        # Tokenize query
        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Pair documents with scores and sort
        doc_scores = list(zip(self.documents, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)

        # Return top results
        results = doc_scores[:limit]

        logger.debug(
            "bm25_search_complete",
            query=query,
            num_results=len(results),
            top_score=results[0][1] if results else 0.0,
        )

        return results

    def search_with_filter(
        self,
        query: str,
        document_ids: set[str],
        limit: int = 20,
    ) -> list[tuple[dict[str, Any], float]]:
        """
        Search with pre-filter to specific document IDs.

        This is used after RBAC filtering - the document_ids come
        from an RBAC-filtered vector search, ensuring we only
        rank documents the user can access.

        Args:
            query: Search query
            document_ids: Set of allowed document IDs (from RBAC filter)
            limit: Maximum results to return

        Returns:
            List of (document, score) tuples for allowed documents only
        """
        if not self.bm25 or not self.documents:
            logger.warning("bm25_filtered_search_no_index")
            return []

        # Tokenize query
        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Filter to allowed documents and pair with scores
        filtered_results = []
        for doc, score in zip(self.documents, scores):
            doc_id = doc.get("document_id", "")
            if doc_id in document_ids:
                filtered_results.append((doc, score))

        # Sort by score
        filtered_results.sort(key=lambda x: x[1], reverse=True)

        # Return top results
        results = filtered_results[:limit]

        logger.debug(
            "bm25_filtered_search_complete",
            query=query,
            allowed_docs=len(document_ids),
            num_results=len(results),
        )

        return results


class BM25Index:
    """
    Persistent BM25 index built from Qdrant collection.

    Loads all documents from Qdrant at startup and maintains
    an in-memory BM25 index for fast sparse retrieval.
    """

    def __init__(self) -> None:
        """Initialize BM25 index."""
        self.retriever = BM25Retriever()
        self._document_map: dict[str, dict[str, Any]] = {}

    async def build_from_qdrant(
        self,
        qdrant_client: Any,  # QdrantVectorStore
        collection_name: str | None = None,
    ) -> int:
        """
        Build BM25 index from Qdrant collection.

        Args:
            qdrant_client: Qdrant client instance
            collection_name: Collection to index (uses default if not specified)

        Returns:
            Number of documents indexed
        """
        from app.core.config import settings

        collection = collection_name or settings.qdrant_collection

        logger.info("building_bm25_index_from_qdrant", collection=collection)

        # Scroll through all documents in Qdrant
        documents = []
        offset = None

        while True:
            # Fetch batch of documents
            results, offset = qdrant_client.client.scroll(
                collection_name=collection,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False,  # We don't need vectors for BM25
            )

            for point in results:
                doc = {
                    "id": point.id,
                    "document_id": point.payload.get("document_id", ""),
                    "text": point.payload.get("text", ""),
                    "title": point.payload.get("title", ""),
                    "chunk_index": point.payload.get("chunk_index", 0),
                    "payload": point.payload,
                }
                documents.append(doc)
                self._document_map[str(point.id)] = doc

            if offset is None:
                break

        # Build BM25 index
        self.retriever.index_documents(documents)

        logger.info(
            "bm25_index_built_from_qdrant",
            num_documents=len(documents),
            collection=collection,
        )

        return len(documents)

    def search(
        self,
        query: str,
        allowed_document_ids: set[str] | None = None,
        limit: int = 20,
    ) -> list[tuple[dict[str, Any], float]]:
        """
        Search BM25 index.

        Args:
            query: Search query
            allowed_document_ids: If provided, filter to these document IDs only
            limit: Maximum results

        Returns:
            List of (document, score) tuples
        """
        if allowed_document_ids is not None:
            return self.retriever.search_with_filter(
                query, allowed_document_ids, limit
            )
        return self.retriever.search(query, limit)
