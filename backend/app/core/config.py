"""Application configuration using pydantic-settings."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "CloudSignal Knowledge Assistant"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cloudsignal"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "documents"

    # OpenAI
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_llm_model: str = "gpt-4o-mini"
    embedding_dimensions: int = 1536

    # Retrieval
    retrieval_top_k: int = 5
    retrieval_initial_k: int = 20
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Chunking
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Security
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60

    # Paths
    data_dir: Path = Path("data")
    rbac_matrix_path: Path = Path("data/metadata/rbac_matrix.json")
    document_manifest_path: Path = Path("data/documents/documents_manifest.json")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def rbac_matrix(self) -> dict[str, Any]:
        """Load RBAC matrix from JSON file."""
        return self._load_json_file(self.rbac_matrix_path)

    @property
    def document_manifest(self) -> dict[str, Any]:
        """Load document manifest from JSON file."""
        return self._load_json_file(self.document_manifest_path)

    @staticmethod
    @lru_cache(maxsize=10)
    def _load_json_file(path: Path) -> dict[str, Any]:
        """Load and cache JSON file."""
        with open(path, encoding="utf-8") as f:
            return json.load(f)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
