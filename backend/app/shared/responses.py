"""
Standardized API Response Helpers

Provides consistent response formatting across all endpoints.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


# ═══════════════════════════════════════════════════════════
# RESPONSE MODELS
# ═══════════════════════════════════════════════════════════

class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""
    page: int
    per_page: int
    total_items: int
    total_pages: int

    @classmethod
    def create(cls, page: int, per_page: int, total_items: int) -> "PaginationMeta":
        """Create pagination metadata."""
        total_pages = (total_items + per_page - 1) // per_page if per_page > 0 else 0
        return cls(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
        )


class ErrorDetail(BaseModel):
    """Error detail structure."""
    code: str
    message: str
    details: dict[str, Any] | None = None


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response."""
    success: bool = True
    data: T
    message: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: ErrorDetail


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""
    success: bool = True
    data: list[T]
    pagination: PaginationMeta
    message: str | None = None


# ═══════════════════════════════════════════════════════════
# RESPONSE HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

def success_response(
    data: Any,
    message: str | None = None,
) -> dict[str, Any]:
    """
    Create a standardized success response.

    Args:
        data: Response data (any type)
        message: Optional success message

    Returns:
        Dictionary with success response structure

    Example:
        return success_response(
            data={"user_id": 1, "username": "john"},
            message="User created successfully"
        )
    """
    response = {
        "success": True,
        "data": data,
    }
    if message:
        response["message"] = message
    return response


def error_response(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a standardized error response.

    Args:
        code: Error code (e.g., "VALIDATION_ERROR", "NOT_FOUND")
        message: Human-readable error message
        details: Optional additional error details

    Returns:
        Dictionary with error response structure

    Example:
        return error_response(
            code="VALIDATION_ERROR",
            message="Invalid email format",
            details={"field": "email", "value": "invalid"}
        )
    """
    error = {
        "code": code,
        "message": message,
    }
    if details:
        error["details"] = details

    return {
        "success": False,
        "error": error,
    }


def paginated_response(
    data: list[Any],
    page: int,
    per_page: int,
    total_items: int,
    message: str | None = None,
) -> dict[str, Any]:
    """
    Create a standardized paginated response.

    Args:
        data: List of items for current page
        page: Current page number (1-indexed)
        per_page: Items per page
        total_items: Total number of items across all pages
        message: Optional message

    Returns:
        Dictionary with paginated response structure

    Example:
        return paginated_response(
            data=[{"id": 1}, {"id": 2}],
            page=1,
            per_page=20,
            total_items=50,
        )
    """
    total_pages = (total_items + per_page - 1) // per_page if per_page > 0 else 0

    response = {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages,
        },
    }
    if message:
        response["message"] = message
    return response


# ═══════════════════════════════════════════════════════════
# ERROR CODES
# ═══════════════════════════════════════════════════════════

class ErrorCodes:
    """Standard error codes used across the application."""

    # Authentication errors
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    SESSION_REVOKED = "SESSION_REVOKED"

    # Authorization errors
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"

    # 2FA errors
    TWO_FACTOR_REQUIRED = "TWO_FACTOR_REQUIRED"
    TWO_FACTOR_INVALID = "TWO_FACTOR_INVALID"
    TWO_FACTOR_NOT_ENABLED = "TWO_FACTOR_NOT_ENABLED"

    # Account errors
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Server errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
