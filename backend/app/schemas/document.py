"""Document-related Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# Access levels
AccessLevel = Literal["public", "internal", "restricted", "confidential"]

# Document status
DocumentStatus = Literal["draft", "active", "deprecated", "archived"]


class ManagerScope(BaseModel):
    """
    Manager scope configuration for documents like performance reviews.

    Used to restrict access to direct reports only.
    """

    direct_reports_only: bool = Field(
        default=False,
        description="If true, only the employee's direct manager can access",
    )
    team_id: str | None = Field(default=None, description="Team ID for team-scoped access")
    employee_id: str | None = Field(
        default=None,
        description="Employee ID for individual-scoped documents (e.g., performance reviews)",
    )


class DocumentMetadata(BaseModel):
    """
    Document metadata stored as Qdrant payload.

    This schema defines all fields used for RBAC filtering at query time.
    """

    # Core identity
    document_id: str = Field(..., description="Unique document identifier (UUID)")
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    doc_type: str = Field(..., description="Document type (e.g., 'postmortem', 'runbook')")
    version: str = Field(default="1.0.0", description="Semantic version")

    # Access control
    access_level: AccessLevel = Field(..., description="Document access level")
    department: str = Field(..., description="Owning department")
    status: DocumentStatus = Field(default="active", description="Document lifecycle status")
    owner_id: str = Field(..., description="Document owner user ID")

    # RBAC fields (stored in Qdrant payload for filtering)
    allowed_roles: list[str] = Field(
        default_factory=list,
        description="Roles allowed to access this document",
    )
    allowed_departments: list[str] = Field(
        default_factory=list,
        description="Departments allowed to access (use ['*'] for all)",
    )
    granted_users: list[str] = Field(
        default_factory=list,
        description="Users explicitly granted access (overrides role denial)",
    )
    denied_users: list[str] = Field(
        default_factory=list,
        description="Users explicitly denied access (highest priority)",
    )

    # Temporal filtering
    available_from: datetime | None = Field(
        default=None,
        description="Embargo date - document not visible before this date",
    )
    available_until: datetime | None = Field(
        default=None,
        description="Expiration date - document not visible after this date",
    )
    created_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Document creation date",
    )
    last_modified: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last modification date",
    )

    # Manager scope (for performance reviews, etc.)
    manager_scope: ManagerScope | None = Field(
        default=None,
        description="Manager-specific access scope",
    )

    # Content metadata
    summary: str | None = Field(default=None, description="Brief document summary")
    keywords: list[str] = Field(default_factory=list, description="Document keywords/tags")
    file_path: str | None = Field(default=None, description="Original file path")
    file_format: str = Field(default=".md", description="File format")

    # Audit
    requires_audit_log: bool = Field(
        default=False,
        description="Whether access should be logged for audit",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "document_id": "doc-eng-coding-python",
                    "title": "Python Coding Standards",
                    "doc_type": "coding_standards",
                    "version": "1.0.0",
                    "access_level": "public",
                    "department": "engineering",
                    "status": "active",
                    "owner_id": "eng-lead-001",
                    "allowed_roles": ["engineer", "sre", "product_manager", "hr", "manager", "admin"],
                    "allowed_departments": ["*"],
                    "keywords": ["python", "coding", "standards", "style"],
                }
            ]
        }
    }


class DocumentChunk(BaseModel):
    """A single chunk of a document with its embedding."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document ID")
    chunk_index: int = Field(..., ge=0, description="Index of this chunk")
    chunk_count: int = Field(..., ge=1, description="Total chunks in document")
    text: str = Field(..., description="Chunk text content")
    metadata: DocumentMetadata = Field(..., description="Document metadata")


class RetrievalResult(BaseModel):
    """Result from document retrieval."""

    document_id: str
    chunk_id: str = Field(default="", description="Unique chunk identifier")
    title: str
    doc_type: str
    department: str
    access_level: AccessLevel
    chunk_index: int
    chunk_count: int = Field(default=1, description="Total chunks in document")
    text: str
    score: float = Field(..., description="Relevance score (rerank or vector)")
    vector_score: float = Field(default=0.0, description="Vector similarity score")
    citation: str | None = Field(default=None, description="Citation reference")

    model_config = {"from_attributes": True}


class DocumentList(BaseModel):
    """Response containing a list of documents."""

    documents: list[RetrievalResult] = Field(
        default_factory=list,
        description="List of documents",
    )
    total: int = Field(..., description="Total number of documents")
    trace_id: str | None = Field(default=None, description="Request trace ID")
