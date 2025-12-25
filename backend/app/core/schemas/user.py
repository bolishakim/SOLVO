"""
User Schemas

Request and response schemas for user operations.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.shared.validators import validate_name, validate_phone_number, validate_password, validate_username


# ═══════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ═══════════════════════════════════════════════════════════


class UserCreate(BaseModel):
    """Schema for creating a new user (internal use)."""

    username: str
    email: EmailStr
    password_hash: str
    first_name: str
    last_name: str
    phone_number: str | None = None


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="First name",
    )
    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Last name",
    )
    phone_number: str | None = Field(
        default=None,
        max_length=20,
        description="Phone number",
    )

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_field(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid, error = validate_name(v)
        if not valid:
            raise ValueError(error)
        return v.strip()

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid, error = validate_phone_number(v)
        if not valid:
            raise ValueError(error)
        return v


class UserAdminCreate(BaseModel):
    """Schema for admin creating a new user."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username (3-50 chars, alphanumeric with underscore/hyphen)",
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 chars, uppercase, lowercase, digit)",
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="First name",
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Last name",
    )
    phone_number: str | None = Field(
        default=None,
        max_length=20,
        description="Optional phone number",
    )
    is_active: bool = Field(
        default=True,
        description="Account active status",
    )
    is_verified: bool = Field(
        default=True,
        description="Email verification status (skip email verification for admin-created users)",
    )
    role_ids: list[int] = Field(
        default_factory=list,
        description="List of role IDs to assign to the user",
    )

    @field_validator("username")
    @classmethod
    def validate_username_format(cls, v: str) -> str:
        valid, error = validate_username(v)
        if not valid:
            raise ValueError(error)
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        valid, error = validate_password(v)
        if not valid:
            raise ValueError(error)
        return v

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_field(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class UserAdminUpdate(BaseModel):
    """Schema for admin updating a user."""

    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone_number: str | None = Field(default=None, max_length=20)
    is_active: bool | None = Field(default=None, description="Account active status")
    is_verified: bool | None = Field(default=None, description="Email verification status")


class RoleAssignRequest(BaseModel):
    """Schema for assigning a role to a user."""

    role_code: str = Field(..., description="Role code to assign")


class RoleRemoveRequest(BaseModel):
    """Schema for removing a role from a user."""

    role_code: str = Field(..., description="Role code to remove")


class SetUserRolesRequest(BaseModel):
    """Schema for setting all roles for a user."""

    role_ids: list[int] = Field(
        ...,
        min_length=1,
        description="List of role IDs to assign (replaces all existing roles)",
    )


# ═══════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════


class RoleResponse(BaseModel):
    """Schema for role in responses."""

    role_id: int
    role_name: str
    role_code: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Schema for user in responses."""

    user_id: int
    username: str
    email: str
    first_name: str
    last_name: str
    phone_number: str | None = None
    is_active: bool
    is_verified: bool
    two_factor_enabled: bool
    created_at: datetime
    last_login_at: datetime | None = None

    class Config:
        from_attributes = True


class UserWithRolesResponse(BaseModel):
    """Schema for user with roles in responses."""

    user_id: int
    username: str
    email: str
    first_name: str
    last_name: str
    phone_number: str | None = None
    is_active: bool
    is_verified: bool
    two_factor_enabled: bool
    created_at: datetime
    last_login_at: datetime | None = None
    roles: list[str] = Field(default_factory=list, description="List of role names")

    class Config:
        from_attributes = True


class UserBriefResponse(BaseModel):
    """Brief user info for token responses."""

    user_id: int
    username: str
    email: str
    first_name: str
    last_name: str
    roles: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CurrentUserResponse(BaseModel):
    """Schema for current user response."""

    success: bool = Field(default=True)
    data: UserWithRolesResponse


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""

    success: bool = Field(default=True)
    data: list[UserWithRolesResponse]
    pagination: dict


class UserDetailResponse(BaseModel):
    """Schema for single user detail response."""

    success: bool = Field(default=True)
    data: UserWithRolesResponse


class RoleListResponse(BaseModel):
    """Schema for list of roles response."""

    success: bool = Field(default=True)
    data: list[RoleResponse]


class RoleDetailResponse(BaseModel):
    """Schema for role with user count."""

    role_id: int
    role_name: str
    role_code: str
    description: str | None = None
    user_count: int = 0

    class Config:
        from_attributes = True


class RolesWithCountResponse(BaseModel):
    """Schema for roles list with user counts."""

    success: bool = Field(default=True)
    data: list[RoleDetailResponse]


class UserRoleAssignResponse(BaseModel):
    """Schema for role assignment response."""

    success: bool = Field(default=True)
    data: dict
    message: str


class UserRolesResponse(BaseModel):
    """Schema for user's roles response."""

    success: bool = Field(default=True)
    data: list[RoleResponse]
