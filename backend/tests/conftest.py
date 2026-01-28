"""Pytest configuration and shared fixtures."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from app.schemas.user import UserContext


# Paths to test data
DATA_DIR = Path(__file__).parent.parent.parent / "data"
RBAC_MATRIX_PATH = DATA_DIR / "metadata" / "rbac_matrix.json"
SECURITY_TESTS_PATH = DATA_DIR / "evaluation" / "security_tests.json"
QA_PAIRS_PATH = DATA_DIR / "evaluation" / "qa_pairs.json"


@pytest.fixture
def rbac_matrix() -> dict[str, Any]:
    """Load RBAC matrix configuration."""
    with open(RBAC_MATRIX_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def security_test_cases() -> list[dict[str, Any]]:
    """Load security test cases."""
    with open(SECURITY_TESTS_PATH, encoding="utf-8") as f:
        data = json.load(f)
        return data.get("security_tests", [])


@pytest.fixture
def qa_pairs() -> list[dict[str, Any]]:
    """Load QA evaluation pairs."""
    with open(QA_PAIRS_PATH, encoding="utf-8") as f:
        data = json.load(f)
        return data.get("qa_pairs", [])


# User context fixtures for each role
@pytest.fixture
def engineer_user() -> UserContext:
    """Engineer role user context."""
    return UserContext(
        user_id="test-engineer-001",
        email="engineer@cloudsignal.io",
        role="engineer",
        department="engineering",
        managed_employees=[],
    )


@pytest.fixture
def sre_user() -> UserContext:
    """SRE role user context."""
    return UserContext(
        user_id="test-sre-001",
        email="sre@cloudsignal.io",
        role="sre",
        department="sre",
        managed_employees=[],
    )


@pytest.fixture
def product_manager_user() -> UserContext:
    """Product Manager role user context."""
    return UserContext(
        user_id="test-pm-001",
        email="pm@cloudsignal.io",
        role="product_manager",
        department="product",
        managed_employees=[],
    )


@pytest.fixture
def hr_user() -> UserContext:
    """HR role user context."""
    return UserContext(
        user_id="test-hr-001",
        email="hr@cloudsignal.io",
        role="hr",
        department="hr",
        managed_employees=[],
    )


@pytest.fixture
def manager_user() -> UserContext:
    """Manager role user context with managed employees."""
    return UserContext(
        user_id="test-manager-001",
        email="manager@cloudsignal.io",
        role="manager",
        department="engineering",
        managed_employees=["emp-001", "emp-002", "emp-003"],
    )


@pytest.fixture
def admin_user() -> UserContext:
    """Admin role user context."""
    return UserContext(
        user_id="test-admin-001",
        email="admin@cloudsignal.io",
        role="admin",
        department="leadership",
        managed_employees=[],
    )


@pytest.fixture
def all_users(
    engineer_user: UserContext,
    sre_user: UserContext,
    product_manager_user: UserContext,
    hr_user: UserContext,
    manager_user: UserContext,
    admin_user: UserContext,
) -> dict[str, UserContext]:
    """Dictionary of all user contexts by role."""
    return {
        "engineer": engineer_user,
        "sre": sre_user,
        "product_manager": product_manager_user,
        "hr": hr_user,
        "manager": manager_user,
        "admin": admin_user,
    }


@pytest.fixture
def current_time() -> datetime:
    """Current time for temporal filtering tests."""
    return datetime.utcnow()


@pytest.fixture
def sample_document_payload() -> dict[str, Any]:
    """Sample document payload for testing."""
    return {
        "document_id": "test-doc-001",
        "title": "Test Document",
        "doc_type": "policy",
        "version": "1.0.0",
        "access_level": "internal",
        "department": "engineering",
        "status": "active",
        "owner_id": "owner-001",
        "allowed_roles": ["engineer", "sre"],
        "allowed_departments": ["engineering", "sre"],
        "granted_users": [],
        "denied_users": [],
        "available_from": None,
        "available_until": None,
        "text": "This is test document content.",
    }


@pytest.fixture
def confidential_hr_document() -> dict[str, Any]:
    """Confidential HR document for security testing."""
    return {
        "document_id": "hr-confidential-001",
        "title": "Salary Bands 2024",
        "doc_type": "salary_band",
        "version": "1.0.0",
        "access_level": "confidential",
        "department": "hr",
        "status": "active",
        "owner_id": "hr-director-001",
        "allowed_roles": ["hr", "manager", "admin"],
        "allowed_departments": ["hr"],
        "granted_users": [],
        "denied_users": [],
        "text": "Executive salary: $500,000. Engineer L5: $250,000-$300,000.",
    }


@pytest.fixture
def deprecated_document() -> dict[str, Any]:
    """Deprecated document for status filtering tests."""
    return {
        "document_id": "deprecated-doc-001",
        "title": "Legacy API Guide",
        "doc_type": "api_doc",
        "version": "0.9.0",
        "access_level": "internal",
        "department": "engineering",
        "status": "deprecated",
        "owner_id": "eng-001",
        "allowed_roles": ["engineer", "sre"],
        "allowed_departments": ["engineering"],
        "granted_users": [],
        "denied_users": [],
        "text": "This API is deprecated. Use v2 instead.",
    }


@pytest.fixture
def embargoed_document() -> dict[str, Any]:
    """Embargoed document for temporal filtering tests."""
    return {
        "document_id": "embargoed-doc-001",
        "title": "Q3 Roadmap",
        "doc_type": "product_roadmap",
        "version": "1.0.0",
        "access_level": "restricted",
        "department": "product",
        "status": "active",
        "owner_id": "pm-001",
        "allowed_roles": ["product_manager", "admin"],
        "allowed_departments": ["product", "leadership"],
        "granted_users": [],
        "denied_users": [],
        "available_from": "2025-03-01T00:00:00Z",  # Future date
        "available_until": None,
        "text": "Q3 secret feature: AI-powered monitoring.",
    }


@pytest.fixture
def manager_scoped_document() -> dict[str, Any]:
    """Manager-scoped performance review document."""
    return {
        "document_id": "perf-review-emp-001",
        "title": "Performance Review - John Doe",
        "doc_type": "performance_review",
        "version": "1.0.0",
        "access_level": "confidential",
        "department": "hr",
        "status": "active",
        "owner_id": "hr-001",
        "allowed_roles": ["hr", "manager", "admin"],
        "allowed_departments": ["hr"],
        "granted_users": [],
        "denied_users": [],
        "manager_scope": {
            "direct_reports_only": True,
            "employee_id": "emp-001",
        },
        "text": "Performance rating: Exceeds expectations. Compensation increase: 15%.",
    }
