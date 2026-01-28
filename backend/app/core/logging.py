"""Structured logging configuration using structlog."""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from app.core.config import settings


def setup_logging() -> None:
    """Configure structured JSON logging."""
    # Set log level based on environment
    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Shared processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.debug:
        # Development: pretty console output
        processors: list[Processor] = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # Production: JSON output
        processors = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """Bind context variables to all subsequent log calls."""
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()


# Security-specific logging helpers
class SecurityLogger:
    """Logger for security-relevant events."""

    def __init__(self) -> None:
        self.logger = get_logger("security")

    def log_access_denied(
        self,
        user_id: str,
        role: str,
        document_id: str | None,
        doc_type: str | None,
        reason: str,
        trace_id: str,
    ) -> None:
        """Log access denial for audit trail."""
        self.logger.warning(
            "access_denied",
            user_id=user_id,
            role=role,
            document_id=document_id,
            doc_type=doc_type,
            reason=reason,
            trace_id=trace_id,
            event_type="rbac_denial",
        )

    def log_confidential_access(
        self,
        user_id: str,
        role: str,
        document_id: str,
        doc_type: str,
        access_level: str,
        trace_id: str,
    ) -> None:
        """Log access to confidential documents."""
        self.logger.info(
            "confidential_document_accessed",
            user_id=user_id,
            role=role,
            document_id=document_id,
            doc_type=doc_type,
            access_level=access_level,
            trace_id=trace_id,
            event_type="confidential_access",
        )

    def log_prompt_injection_attempt(
        self,
        user_id: str,
        query: str,
        detection_reason: str,
        trace_id: str,
    ) -> None:
        """Log potential prompt injection attempt."""
        self.logger.warning(
            "prompt_injection_detected",
            user_id=user_id,
            query_preview=query[:100] if len(query) > 100 else query,
            detection_reason=detection_reason,
            trace_id=trace_id,
            event_type="security_alert",
        )

    def log_query(
        self,
        user_id: str,
        role: str,
        query: str,
        result_count: int,
        trace_id: str,
    ) -> None:
        """Log user query for audit."""
        self.logger.info(
            "user_query",
            user_id=user_id,
            role=role,
            query_preview=query[:100] if len(query) > 100 else query,
            result_count=result_count,
            trace_id=trace_id,
            event_type="query",
        )


security_logger = SecurityLogger()
