"""Document ingestion service."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from qdrant_client.models import PointStruct

from app.core.config import settings
from app.core.logging import get_logger
from app.services.ingestion.chunker import TextChunker
from app.services.ingestion.embedder import EmbeddingGenerator
from app.services.ingestion.parser import DocumentParser
from app.vector_store.qdrant_client import QdrantVectorStore

logger = get_logger(__name__)


class IngestionService:
    """
    Orchestrate document ingestion pipeline.

    Pipeline steps:
    1. Load document manifest
    2. Parse each document
    3. Chunk text
    4. Generate embeddings
    5. Store in Qdrant with RBAC metadata
    """

    def __init__(
        self,
        parser: DocumentParser | None = None,
        chunker: TextChunker | None = None,
        embedder: EmbeddingGenerator | None = None,
        vector_store: QdrantVectorStore | None = None,
    ) -> None:
        """
        Initialize ingestion service.

        Args:
            parser: Document parser (optional, creates default)
            chunker: Text chunker (optional, creates default)
            embedder: Embedding generator (optional, creates default)
            vector_store: Qdrant client (optional, creates default)
        """
        self.parser = parser or DocumentParser()
        self.chunker = chunker or TextChunker()
        self.embedder = embedder or EmbeddingGenerator()
        self.vector_store = vector_store or QdrantVectorStore()

        logger.info("ingestion_service_initialized")

    async def ingest_document(
        self,
        file_path: str | Path,
        metadata: dict[str, Any],
    ) -> int:
        """
        Ingest a single document.

        Args:
            file_path: Path to document file
            metadata: Document metadata from manifest

        Returns:
            Number of chunks created
        """
        document_id = metadata.get("document_id", "unknown")

        try:
            # 1. Parse document
            text = self.parser.parse(file_path)

            if not text.strip():
                logger.warning("empty_document", document_id=document_id)
                return 0

            # 2. Chunk text
            chunks = self.chunker.chunk_with_metadata(text, document_id)

            if not chunks:
                logger.warning("no_chunks_created", document_id=document_id)
                return 0

            # 3. Generate embeddings
            chunk_texts = [c["text"] for c in chunks]
            embeddings = await self.embedder.embed_batch(chunk_texts)

            # 4. Prepare points for Qdrant
            points = []
            for chunk, embedding in zip(chunks, embeddings):
                if not embedding:
                    continue

                # Build payload with all metadata for RBAC filtering
                payload = self._build_payload(metadata, chunk)

                point = PointStruct(
                    id=chunk["chunk_id"],
                    vector=embedding,
                    payload=payload,
                )
                points.append(point)

            # 5. Store in Qdrant
            if points:
                await self.vector_store.upsert_points(points)

            logger.info(
                "document_ingested",
                document_id=document_id,
                chunks_created=len(points),
                file_path=str(file_path),
            )

            return len(points)

        except Exception as e:
            logger.error(
                "ingestion_failed",
                document_id=document_id,
                file_path=str(file_path),
                error=str(e),
            )
            raise

    def _build_payload(
        self,
        metadata: dict[str, Any],
        chunk: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build Qdrant payload with all RBAC fields.

        This payload must contain all fields needed for:
        - RBAC filtering at query time
        - Document display and citation
        - Audit logging
        """
        # Start with document metadata
        payload = {
            # Core identity
            "document_id": metadata.get("document_id"),
            "title": metadata.get("title"),
            "doc_type": metadata.get("doc_type"),
            "version": metadata.get("version", "1.0.0"),
            # Access control
            "access_level": metadata.get("access_level"),
            "department": metadata.get("department"),
            "status": metadata.get("status", "active"),
            "owner_id": metadata.get("owner_id"),
            # RBAC fields
            "allowed_roles": metadata.get("allowed_roles", []),
            "allowed_departments": metadata.get("allowed_departments", []),
            "granted_users": metadata.get("granted_users", []),
            "denied_users": metadata.get("denied_users", []),
            # Temporal fields
            "available_from": metadata.get("available_from"),
            "available_until": metadata.get("available_until"),
            "created_date": metadata.get("created_date"),
            "last_modified": metadata.get("last_modified", datetime.utcnow().isoformat()),
            # Manager scope
            "manager_scope": metadata.get("manager_scope"),
            # Content metadata
            "summary": metadata.get("summary"),
            "keywords": metadata.get("keywords", []),
            "file_path": metadata.get("file_path"),
            "file_format": metadata.get("file_format", ".md"),
            # Audit
            "requires_audit_log": metadata.get("requires_audit_log", False),
            # Chunk info
            "chunk_index": chunk.get("chunk_index", 0),
            "chunk_count": chunk.get("chunk_count", 1),
            "text": chunk.get("text", ""),
        }

        return payload

    async def ingest_from_manifest(
        self,
        manifest_path: str | Path | None = None,
        base_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Ingest all documents from manifest file.

        Args:
            manifest_path: Path to documents_manifest.json
            base_path: Base path for document files

        Returns:
            Ingestion results summary
        """
        manifest_path = Path(manifest_path or settings.document_manifest_path)
        base_path = Path(base_path or settings.data_dir / "documents")

        logger.info(
            "starting_manifest_ingestion",
            manifest_path=str(manifest_path),
            base_path=str(base_path),
        )

        # Load manifest
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)

        documents = manifest.get("documents", [])

        results = {
            "total": len(documents),
            "success": 0,
            "failed": 0,
            "total_chunks": 0,
            "errors": [],
        }

        # Ensure collection exists
        await self.vector_store.create_collection()

        # Process each document
        for doc in documents:
            document_id = doc.get("document_id", "unknown")
            file_path = doc.get("file_path", "")

            try:
                # Build full file path
                full_path = base_path / file_path

                if not full_path.exists():
                    logger.warning(
                        "document_file_not_found",
                        document_id=document_id,
                        file_path=str(full_path),
                    )
                    results["failed"] += 1
                    results["errors"].append(
                        {"document_id": document_id, "error": "File not found"}
                    )
                    continue

                # Ingest document
                chunks = await self.ingest_document(full_path, doc)
                results["success"] += 1
                results["total_chunks"] += chunks

            except Exception as e:
                logger.error(
                    "document_ingestion_error",
                    document_id=document_id,
                    error=str(e),
                )
                results["failed"] += 1
                results["errors"].append({"document_id": document_id, "error": str(e)})

        logger.info(
            "manifest_ingestion_complete",
            **{k: v for k, v in results.items() if k != "errors"},
        )

        return results

    async def reingest_document(
        self,
        document_id: str,
        manifest_path: str | Path | None = None,
    ) -> int:
        """
        Re-ingest a specific document (delete and recreate).

        Args:
            document_id: Document ID to reingest
            manifest_path: Path to manifest file

        Returns:
            Number of chunks created
        """
        manifest_path = Path(manifest_path or settings.document_manifest_path)

        # Load manifest
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)

        # Find document in manifest
        doc = None
        for d in manifest.get("documents", []):
            if d.get("document_id") == document_id:
                doc = d
                break

        if not doc:
            raise ValueError(f"Document not found in manifest: {document_id}")

        # Delete existing chunks
        await self.vector_store.delete_document(document_id)

        # Re-ingest
        base_path = Path(settings.data_dir / "documents")
        full_path = base_path / doc.get("file_path", "")

        return await self.ingest_document(full_path, doc)
