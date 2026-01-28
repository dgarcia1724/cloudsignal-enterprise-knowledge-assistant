"""User-related Pydantic schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

# Valid roles for RBAC
RoleType = Literal["engineer", "sre", "product_manager", "hr", "manager", "admin"]

# Valid departments
DepartmentType = Literal["engineering", "sre", "product", "hr", "leadership", "operations"]


class UserContext(BaseModel):
    """
    User context for RBAC filtering.

    This represents the authenticated user making a request.
    Used to build Qdrant filters for retrieval-time access control.
    """

    user_id: str = Field(..., description="Unique user identifier (e.g., 'eng-alice-001')")
    role: RoleType = Field(..., description="User's role for RBAC")
    department: str = Field(..., description="User's department")
    managed_employees: list[str] = Field(
        default_factory=list,
        description="Employee IDs this user manages (for managers)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "eng-alice-001",
                    "role": "engineer",
                    "department": "engineering",
                    "managed_employees": [],
                },
                {
                    "user_id": "mgr-sarah-chen",
                    "role": "manager",
                    "department": "engineering",
                    "managed_employees": ["eng-js-001", "eng-bob-002"],
                },
            ]
        }
    }


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    id: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: RoleType
    department: str
    managed_employees: list[str] = Field(default_factory=list)


class UserResponse(BaseModel):
    """Schema for user response (excludes password)."""

    id: str
    email: str
    role: RoleType
    department: str
    managed_employees: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
