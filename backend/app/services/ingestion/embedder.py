"""Embedding generation using OpenAI API."""

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingGenerator:
    """
    Generate embeddings using OpenAI text-embedding-3-small.

    This model provides a good balance of quality and cost:
    - 1536 dimensions
    - $0.00002 per 1K tokens
    - Excellent semantic understanding
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        """
        Initialize embedding generator.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: Embedding model name (defaults to settings)
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_embedding_model
        self.dimensions = settings.embedding_dimensions

        self.client = AsyncOpenAI(api_key=self.api_key)

        logger.info(
            "embedder_initialized",
            model=self.model,
            dimensions=self.dimensions,
        )

    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )

        embedding = response.data[0].embedding

        logger.debug(
            "text_embedded",
            text_length=len(text),
            embedding_dim=len(embedding),
            tokens_used=response.usage.total_tokens,
        )

        return embedding

    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        The OpenAI API supports batch embedding, which is more efficient
        than individual requests.

        Args:
            texts: List of texts to embed
            batch_size: Maximum texts per API call

        Returns:
            List of embedding vectors (same order as input)
        """
        if not texts:
            return []

        # Filter empty texts and track positions
        non_empty_texts = []
        positions = []
        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_texts.append(text)
                positions.append(i)

        if not non_empty_texts:
            return [[] for _ in texts]

        # Process in batches
        all_embeddings: list[list[float]] = []

        for i in range(0, len(non_empty_texts), batch_size):
            batch = non_empty_texts[i : i + batch_size]

            response = await self.client.embeddings.create(
                model=self.model,
                input=batch,
            )

            # Extract embeddings in order
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

            logger.debug(
                "batch_embedded",
                batch_size=len(batch),
                tokens_used=response.usage.total_tokens,
            )

        # Reconstruct full list with empty embeddings for empty texts
        result: list[list[float]] = [[] for _ in texts]
        for pos, embedding in zip(positions, all_embeddings):
            result[pos] = embedding

        logger.info(
            "batch_embedding_complete",
            total_texts=len(texts),
            embedded_texts=len(non_empty_texts),
        )

        return result

    async def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.

        This is an alias for embed() but may include query-specific
        preprocessing in the future.

        Args:
            query: Search query text

        Returns:
            Query embedding vector
        """
        return await self.embed(query)
