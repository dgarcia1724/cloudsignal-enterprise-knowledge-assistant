"""Dependency injection for FastAPI routes."""

import uuid
from typing import Annotated, Any, AsyncGenerator

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db_session
from app.schemas.user import UserContext


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in get_db_session():
        yield session


def get_trace_id(request: Request) -> str:
    """Extract or generate trace ID for request tracking."""
    trace_id = request.headers.get("X-Trace-ID")
    if not trace_id:
        trace_id = str(uuid.uuid4())
    return trace_id


async def get_current_user(
    request: Request,
    x_user_id: Annotated[str | None, Header()] = None,
    x_user_role: Annotated[str | None, Header()] = None,
    x_user_department: Annotated[str | None, Header()] = None,
    x_managed_employees: Annotated[str | None, Header()] = None,
) -> UserContext:
    """
    Extract user context from request headers.

    In production, this would validate JWT tokens and extract user info.
    For development/testing, we accept user context via headers.

    Headers:
        X-User-ID: User identifier (e.g., "eng-alice-001")
        X-User-Role: User role (engineer, sre, product_manager, hr, manager, admin)
        X-User-Department: User department
        X-Managed-Employees: Comma-separated list of managed employee IDs (for managers)
    """
    # For development, allow header-based auth
    if settings.debug or settings.environment == "development":
        if x_user_id and x_user_role and x_user_department:
            managed_employees: list[str] = []
            if x_managed_employees:
                managed_employees = [e.strip() for e in x_managed_employees.split(",")]

            return UserContext(
                user_id=x_user_id,
                role=x_user_role,  # type: ignore[arg-type]
                department=x_user_department,
                managed_employees=managed_employees,
            )

    # Check if user context is set by middleware (e.g., from JWT)
    user_context = getattr(request.state, "user", None)
    if user_context:
        return user_context

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_admin_user(
    current_user: Annotated[UserContext, Depends(get_current_user)],
) -> UserContext:
    """Require admin role for the endpoint."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def get_rbac_matrix() -> dict[str, Any]:
    """Get RBAC matrix configuration."""
    return settings.rbac_matrix


# Type aliases for cleaner dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[UserContext, Depends(get_current_user)]
AdminUser = Annotated[UserContext, Depends(get_admin_user)]
TraceId = Annotated[str, Depends(get_trace_id)]
RBACMatrix = Annotated[dict[str, Any], Depends(get_rbac_matrix)]
