"""Text chunking for document ingestion."""

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TextChunker:
    """
    Split documents into overlapping chunks for embedding.

    Uses recursive character splitting with configurable chunk size and overlap.
    Tries to split on natural boundaries (paragraphs, sentences) when possible.
    """

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        separators: list[str] | None = None,
    ) -> None:
        """
        Initialize chunker.

        Args:
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks
            separators: List of separators to try, in order of preference
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", ", ", " ", ""]

        logger.debug(
            "chunker_initialized",
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

    def chunk(self, text: str) -> list[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        text = text.strip()

        # If text is smaller than chunk size, return as single chunk
        if len(text) <= self.chunk_size:
            return [text]

        chunks = self._recursive_split(text, self.separators)

        # Merge small chunks and ensure overlap
        merged_chunks = self._merge_chunks(chunks)

        logger.debug(
            "text_chunked",
            input_length=len(text),
            num_chunks=len(merged_chunks),
            avg_chunk_size=sum(len(c) for c in merged_chunks) // len(merged_chunks)
            if merged_chunks
            else 0,
        )

        return merged_chunks

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using separators."""
        if not separators:
            # No more separators, split by character
            return self._split_by_size(text)

        separator = separators[0]
        remaining_separators = separators[1:]

        # Split on current separator
        splits = text.split(separator) if separator else list(text)

        # Process each split
        chunks = []
        for split in splits:
            if not split:
                continue

            if len(split) <= self.chunk_size:
                chunks.append(split)
            else:
                # Recursively split with remaining separators
                chunks.extend(self._recursive_split(split, remaining_separators))

        return chunks

    def _split_by_size(self, text: str) -> list[str]:
        """Split text into fixed-size chunks."""
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i : i + self.chunk_size]
            if chunk:
                chunks.append(chunk)
        return chunks

    def _merge_chunks(self, chunks: list[str]) -> list[str]:
        """
        Merge small chunks and add overlap between chunks.

        This ensures:
        - No chunk is too small (unless it's the last one)
        - Adjacent chunks have overlapping content for context
        """
        if not chunks:
            return []

        merged = []
        current_chunk = ""

        for chunk in chunks:
            # If adding this chunk exceeds size, save current and start new
            if len(current_chunk) + len(chunk) + 1 > self.chunk_size:
                if current_chunk:
                    merged.append(current_chunk.strip())

                    # Start new chunk with overlap from previous
                    if self.chunk_overlap > 0:
                        overlap_text = current_chunk[-self.chunk_overlap :]
                        current_chunk = overlap_text + " " + chunk
                    else:
                        current_chunk = chunk
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += " " + chunk
                else:
                    current_chunk = chunk

        # Don't forget the last chunk
        if current_chunk:
            merged.append(current_chunk.strip())

        return merged

    def chunk_with_metadata(
        self,
        text: str,
        document_id: str,
    ) -> list[dict[str, str | int]]:
        """
        Chunk text and return with metadata.

        Args:
            text: Text to chunk
            document_id: Document identifier

        Returns:
            List of dicts with chunk text and metadata
        """
        chunks = self.chunk(text)

        return [
            {
                "chunk_id": f"{document_id}_{i}",
                "document_id": document_id,
                "chunk_index": i,
                "chunk_count": len(chunks),
                "text": chunk,
            }
            for i, chunk in enumerate(chunks)
        ]
