"""
RBAC Filter Builder for Qdrant.

CRITICAL SECURITY COMPONENT: This module builds Qdrant filters that enforce
access control at query time, BEFORE vector search. This ensures unauthorized
documents never enter the retrieval pipeline or LLM context.

Security Design:
- Filters are applied as Qdrant query_filter parameter
- Access is evaluated with priority: denied_users > granted_users > role > department > public
- Manager-scoped documents (e.g., performance reviews) require additional checks
- Temporal filtering enforces embargo and expiration dates
"""

from datetime import datetime, timezone
from typing import Any

from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    Range,
)

from app.core.logging import get_logger, security_logger
from app.schemas.user import UserContext

logger = get_logger(__name__)


class RBACFilterBuilder:
    """
    Builds Qdrant filters for retrieval-time RBAC enforcement.

    CRITICAL: These filters must be applied at query time, not post-retrieval.
    This ensures unauthorized documents never enter the LLM context.

    Usage:
        builder = RBACFilterBuilder(rbac_matrix)
        filter = builder.build_filter(user_context)
        results = qdrant.search(query_vector, query_filter=filter)
    """

    def __init__(self, rbac_matrix: dict[str, Any]) -> None:
        """
        Initialize filter builder with RBAC configuration.

        Args:
            rbac_matrix: RBAC matrix loaded from data/metadata/rbac_matrix.json
        """
        self.rbac_matrix = rbac_matrix.get("rbac_matrix", {})
        self.access_levels = rbac_matrix.get("access_levels", {})
        logger.info("rbac_filter_builder_initialized", roles=list(self.rbac_matrix.keys()))

    def build_filter(
        self,
        user_context: UserContext,
        current_time: datetime | None = None,
    ) -> Filter:
        """
        Build a complete RBAC filter for the given user.

        Filter Priority (highest to lowest):
        1. Explicit denials (denied_users) - blocks even granted users
        2. Explicit grants (granted_users) - overrides role-based denial
        3. Role-based access (allowed_roles)
        4. Department-based access (allowed_departments)
        5. Public documents (access_level = public)

        Args:
            user_context: Authenticated user's context
            current_time: Current time for temporal filtering (defaults to UTC now)

        Returns:
            Qdrant Filter object to apply at query time
        """
        current_time = current_time or datetime.now(timezone.utc)
        role_config = self.rbac_matrix.get(user_context.role, {})

        logger.debug(
            "building_rbac_filter",
            user_id=user_context.user_id,
            role=user_context.role,
            department=user_context.department,
        )

        # Build must conditions (all must be true)
        must_conditions: list[Filter | FieldCondition] = []

        # 1. Exclude explicitly denied users (highest priority)
        must_conditions.append(self._build_denial_exclusion(user_context.user_id))

        # 2. Status filter (active by default, deprecated for certain roles)
        must_conditions.append(self._build_status_filter(user_context, role_config))

        # 3. Temporal filter (embargo and expiration)
        temporal_filter = self._build_temporal_filter(current_time)
        if temporal_filter:
            must_conditions.append(temporal_filter)

        # Build should conditions (at least one must be true for access)
        should_conditions: list[FieldCondition] = []

        # 4. Admin bypass - admins can access everything
        if user_context.role == "admin":
            # Return minimal filter for admin (just status and temporal)
            return Filter(must=must_conditions)

        # 5. Public access (available to all authenticated users)
        should_conditions.append(
            FieldCondition(key="access_level", match=MatchValue(value="public"))
        )

        # 6. Explicit user grant (overrides role-based denial)
        should_conditions.append(
            FieldCondition(key="granted_users", match=MatchAny(any=[user_context.user_id]))
        )

        # 7. Role-based access
        should_conditions.append(
            FieldCondition(key="allowed_roles", match=MatchAny(any=[user_context.role]))
        )

        # 8. Department-based access (for internal documents)
        dept_filter = self._build_department_access_filter(user_context, role_config)
        if dept_filter:
            should_conditions.append(dept_filter)

        # 9. Manager scope filter for performance reviews
        if user_context.role == "manager" and user_context.managed_employees:
            manager_filter = self._build_manager_scope_filter(user_context)
            if manager_filter:
                should_conditions.append(manager_filter)

        # Combine filters
        return Filter(
            must=must_conditions,
            should=should_conditions,
        )

    def _build_denial_exclusion(self, user_id: str) -> Filter:
        """
        Exclude documents where user is explicitly denied.

        CRITICAL: This has highest priority and blocks access even if user
        is otherwise granted access via role or explicit grant.
        """
        return Filter(
            must_not=[FieldCondition(key="denied_users", match=MatchAny(any=[user_id]))]
        )

    def _build_status_filter(
        self,
        user_context: UserContext,
        role_config: dict[str, Any],
    ) -> FieldCondition:
        """
        Filter by document status based on role permissions.

        Most roles only see 'active' documents.
        SRE and Manager can also see 'deprecated' documents.
        Admin can see all statuses.
        """
        can_access_deprecated = role_config.get("can_access_deprecated", False)

        if user_context.role == "admin":
            # Admin sees everything
            return FieldCondition(
                key="status",
                match=MatchAny(any=["active", "draft", "deprecated", "archived"]),
            )
        elif can_access_deprecated:
            # SRE, Manager can see deprecated
            return FieldCondition(key="status", match=MatchAny(any=["active", "deprecated"]))
        else:
            # Most roles only see active
            return FieldCondition(key="status", match=MatchValue(value="active"))

    def _build_temporal_filter(self, current_time: datetime) -> Filter | None:
        """
        Build temporal filter for embargo and expiration dates.

        Documents are filtered out if:
        - available_from is set and is in the future (embargo)
        - available_until is set and is in the past (expired)
        """
        iso_time = current_time.isoformat()

        # Build filter for available_from (embargo)
        # Document is accessible if available_from is null OR <= current_time
        available_from_filter = Filter(
            should=[
                # No embargo date set - always accessible
                FieldCondition(key="available_from", match=MatchValue(value=None)),
                # Embargo date has passed
                FieldCondition(key="available_from", range=Range(lte=iso_time)),
            ]
        )

        # Build filter for available_until (expiration)
        # Document is accessible if available_until is null OR >= current_time
        available_until_filter = Filter(
            should=[
                # No expiration date set - always accessible
                FieldCondition(key="available_until", match=MatchValue(value=None)),
                # Not yet expired
                FieldCondition(key="available_until", range=Range(gte=iso_time)),
            ]
        )

        return Filter(must=[available_from_filter, available_until_filter])

    def _build_department_access_filter(
        self,
        user_context: UserContext,
        role_config: dict[str, Any],
    ) -> FieldCondition | None:
        """
        Build department-based access filter.

        Users can access documents from their allowed departments.
        Documents with allowed_departments = ["*"] are accessible to all.
        """
        allowed_depts = role_config.get("allowed_departments", [])

        if not allowed_depts:
            return None

        # User can access documents that allow their department OR allow all ("*")
        departments_to_check = allowed_depts + ["*"]

        return FieldCondition(
            key="allowed_departments",
            match=MatchAny(any=departments_to_check),
        )

    def _build_manager_scope_filter(self, user_context: UserContext) -> FieldCondition | None:
        """
        Build manager-specific filter for scoped documents.

        CRITICAL: Managers can only access performance reviews of their direct reports.
        This is enforced via the manager_scope.employee_id field in document metadata.

        Returns filter that matches documents where:
        - manager_scope.employee_id is in user's managed_employees list
        """
        if not user_context.managed_employees:
            return None

        # Manager can access documents scoped to their managed employees
        return FieldCondition(
            key="manager_scope.employee_id",
            match=MatchAny(any=user_context.managed_employees),
        )


class RBACService:
    """
    Service for RBAC policy evaluation and audit logging.

    Wraps RBACFilterBuilder with additional business logic:
    - Audit logging for access events
    - Access denial tracking
    - Security event logging
    """

    def __init__(self, rbac_matrix: dict[str, Any]) -> None:
        """Initialize RBAC service with configuration."""
        self.filter_builder = RBACFilterBuilder(rbac_matrix)
        self.rbac_matrix = rbac_matrix.get("rbac_matrix", {})

    def get_query_filter(
        self,
        user_context: UserContext,
        trace_id: str,
    ) -> Filter:
        """
        Get Qdrant filter for user's query.

        Args:
            user_context: Authenticated user context
            trace_id: Request trace ID for logging

        Returns:
            Qdrant Filter for query-time RBAC enforcement
        """
        filter = self.filter_builder.build_filter(user_context)

        logger.info(
            "rbac_filter_created",
            user_id=user_context.user_id,
            role=user_context.role,
            trace_id=trace_id,
        )

        return filter

    def log_document_access(
        self,
        user_context: UserContext,
        document_id: str,
        doc_type: str,
        access_level: str,
        trace_id: str,
    ) -> None:
        """
        Log access to a document for audit trail.

        This should be called after successful retrieval for:
        - Confidential documents (always)
        - Restricted documents (always)
        - Any document with requires_audit_log = true
        """
        if access_level in ("confidential", "restricted"):
            security_logger.log_confidential_access(
                user_id=user_context.user_id,
                role=user_context.role,
                document_id=document_id,
                doc_type=doc_type,
                access_level=access_level,
                trace_id=trace_id,
            )

    def log_access_denied(
        self,
        user_context: UserContext,
        document_id: str | None,
        doc_type: str | None,
        reason: str,
        trace_id: str,
    ) -> None:
        """Log access denial for security audit."""
        security_logger.log_access_denied(
            user_id=user_context.user_id,
            role=user_context.role,
            document_id=document_id,
            doc_type=doc_type,
            reason=reason,
            trace_id=trace_id,
        )

    def can_access_deprecated(self, user_context: UserContext) -> bool:
        """Check if user's role can access deprecated documents."""
        role_config = self.rbac_matrix.get(user_context.role, {})
        return role_config.get("can_access_deprecated", False)

    def get_allowed_access_levels(self, user_context: UserContext) -> list[str]:
        """Get list of access levels the user can access."""
        if user_context.role == "admin":
            return ["public", "internal", "restricted", "confidential"]

        role_config = self.rbac_matrix.get(user_context.role, {})
        return role_config.get("allowed_access_levels", ["public"])

    def get_allowed_departments(self, user_context: UserContext) -> list[str]:
        """Get list of departments the user can access."""
        if user_context.role == "admin":
            return ["*"]

        role_config = self.rbac_matrix.get(user_context.role, {})
        return role_config.get("allowed_departments", [])
