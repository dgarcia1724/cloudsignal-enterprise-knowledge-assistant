"""Audit log model for security event tracking."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base):
    """
    Audit log for tracking security-relevant events.

    This model records:
    - Document access events (especially confidential/restricted)
    - Access denials (RBAC violations)
    - User queries
    - Security alerts (prompt injection attempts)

    Attributes:
        id: Unique audit log entry ID
        user_id: User who triggered the event
        action: Type of action (query, access, denied, security_alert)
        document_id: Document involved (if applicable)
        document_type: Type of document accessed
        access_level: Document access level
        query: User's query text (if applicable)
        result: Outcome (granted, denied, partial)
        reason: Reason for denial (if applicable)
        trace_id: Request trace ID for correlation
        metadata: Additional event metadata as JSON
        timestamp: Event timestamp
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    document_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    document_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    access_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    query: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    trace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, user_id={self.user_id}, "
            f"action={self.action}, result={self.result})>"
        )


# Action types
class AuditAction:
    """Constants for audit log action types."""

    QUERY = "query"
    ACCESS = "access"
    DENIED = "denied"
    SECURITY_ALERT = "security_alert"
    LOGIN = "login"
    LOGOUT = "logout"


# Result types
class AuditResult:
    """Constants for audit log result types."""

    GRANTED = "granted"
    DENIED = "denied"
    PARTIAL = "partial"
    SUCCESS = "success"
    FAILED = "failed"
