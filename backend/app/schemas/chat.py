"""Chat-related Pydantic schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message."""

    role: Literal["user", "assistant", "system"] = Field(..., description="Message sender role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Request payload for chat endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User's question or message",
    )
    conversation_id: str | None = Field(
        default=None,
        description="Optional conversation ID for multi-turn context",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "What is the maximum line length for Python code?",
                    "conversation_id": None,
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    """Full response from chat endpoint (non-streaming)."""

    message: ChatMessage = Field(..., description="Assistant's response message")
    sources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Source documents used to generate answer",
    )
    conversation_id: str | None = Field(default=None, description="Conversation ID for follow-ups")
    trace_id: str | None = Field(default=None, description="Request trace ID for debugging")


class StreamChunk(BaseModel):
    """A single chunk in a streaming response."""

    type: Literal["content", "sources", "done", "error"] = Field(
        ...,
        description="Chunk type",
    )
    content: str | None = Field(default=None, description="Text content (for type='content')")
    sources: list[dict[str, Any]] | None = Field(
        default=None,
        description="Source documents (for type='sources')",
    )
    error: str | None = Field(default=None, description="Error message (for type='error')")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"type": "sources", "sources": [{"document_id": "doc-1", "title": "Python Standards"}]},
                {"type": "content", "content": "The maximum line length"},
                {"type": "content", "content": " is 100 characters."},
                {"type": "done", "content": None},
            ]
        }
    }
