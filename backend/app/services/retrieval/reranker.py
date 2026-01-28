"""Local cross-encoder reranker for two-stage retrieval."""

from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LocalReranker:
    """
    Local cross-encoder reranker using sentence-transformers.

    Uses ms-marco-MiniLM-L-6-v2 for efficient reranking without API costs.
    This model was trained on MS MARCO passage ranking and provides
    excellent quality for document reranking.

    Two-stage retrieval:
    1. First stage: Retrieve top-N candidates (fast, broad recall)
    2. Second stage: Rerank to top-K (accurate, focused precision)
    """

    def __init__(
        self,
        model_name: str | None = None,
    ) -> None:
        """
        Initialize reranker.

        Args:
            model_name: Cross-encoder model name (defaults to settings)
        """
        self.model_name = model_name or settings.reranker_model
        self._model = None
        self._initialized = False

        logger.info("reranker_initialized", model=self.model_name)

    def _ensure_model_loaded(self) -> None:
        """Lazy load the cross-encoder model."""
        if self._initialized:
            return

        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)
            self._initialized = True

            logger.info("reranker_model_loaded", model=self.model_name)

        except ImportError as e:
            logger.error(
                "reranker_import_error",
                error=str(e),
                hint="Install sentence-transformers: pip install sentence-transformers",
            )
            raise

        except Exception as e:
            logger.error(
                "reranker_load_error",
                model=self.model_name,
                error=str(e),
            )
            raise

    def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_k: int = 5,
        text_key: str = "text",
    ) -> list[tuple[dict[str, Any], float]]:
        """
        Rerank documents using cross-encoder.

        Args:
            query: Search query
            documents: List of documents to rerank
            top_k: Number of top results to return
            text_key: Key in document dict containing text

        Returns:
            List of (document, score) tuples sorted by rerank score
        """
        if not documents:
            return []

        self._ensure_model_loaded()

        # Prepare query-document pairs for cross-encoder
        pairs = []
        for doc in documents:
            text = doc.get(text_key, "")
            if text:
                pairs.append([query, text])
            else:
                # Handle missing text gracefully
                pairs.append([query, ""])

        # Get cross-encoder scores
        scores = self._model.predict(pairs)

        # Pair documents with scores
        doc_scores = list(zip(documents, scores))

        # Sort by score descending
        doc_scores.sort(key=lambda x: x[1], reverse=True)

        # Return top-k
        results = doc_scores[:top_k]

        logger.debug(
            "rerank_complete",
            query_length=len(query),
            input_docs=len(documents),
            output_docs=len(results),
            top_score=float(results[0][1]) if results else 0.0,
        )

        return results

    def rerank_with_context(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Rerank and return documents with rerank scores attached.

        This is a convenience method that returns the documents
        with an added 'rerank_score' field.

        Args:
            query: Search query
            documents: List of documents to rerank
            top_k: Number of top results to return

        Returns:
            List of documents with 'rerank_score' field added
        """
        reranked = self.rerank(query, documents, top_k)

        results = []
        for doc, score in reranked:
            doc_with_score = dict(doc)
            doc_with_score["rerank_score"] = float(score)
            results.append(doc_with_score)

        return results


def reciprocal_rank_fusion(
    *result_lists: list[tuple[Any, float]],
    k: int = 60,
) -> list[tuple[Any, float]]:
    """
    Combine multiple ranked lists using Reciprocal Rank Fusion.

    RRF is a simple but effective method to combine rankings from
    different retrieval methods (e.g., BM25 + vector search).

    Formula: RRF(d) = Σ 1 / (k + rank(d))

    Args:
        *result_lists: Variable number of result lists, each containing
                      (document, score) tuples sorted by score descending
        k: RRF constant (default 60, as per original paper)

    Returns:
        List of (document, rrf_score) tuples sorted by RRF score
    """
    # Track RRF scores by document ID
    rrf_scores: dict[str, float] = {}
    doc_map: dict[str, Any] = {}

    for result_list in result_lists:
        for rank, (doc, _score) in enumerate(result_list, start=1):
            # Use document_id as key, falling back to chunk_id or str(doc)
            doc_id = doc.get("document_id", doc.get("chunk_id", str(doc)))

            # RRF formula
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)

            # Keep document reference
            if doc_id not in doc_map:
                doc_map[doc_id] = doc

    # Convert to list and sort by RRF score
    results = [(doc_map[doc_id], score) for doc_id, score in rrf_scores.items()]
    results.sort(key=lambda x: x[1], reverse=True)

    logger.debug(
        "rrf_fusion_complete",
        num_lists=len(result_lists),
        unique_docs=len(results),
    )

    return results
