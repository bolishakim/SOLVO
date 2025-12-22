"""
Custom Exceptions

Application-specific exceptions with HTTP status codes and error details.
"""

from typing import Any

from app.shared.responses import ErrorCodes


class AppException(Exception):
    """
    Base exception for all application errors.

    All custom exceptions should inherit from this class.
    """

    status_code: int = 500
    error_code: str = ErrorCodes.INTERNAL_ERROR
    message: str = "An unexpected error occurred"
    details: dict[str, Any] | None = None

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
        error_code: str | None = None,
    ):
        self.message = message or self.message
        self.details = details or self.details
        if error_code:
            self.error_code = error_code
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to error response dictionary."""
        error = {
            "code": self.error_code,
            "message": self.message,
        }
        if self.details:
            error["details"] = self.details

        return {
            "success": False,
            "error": error,
        }


# ═══════════════════════════════════════════════════════════
# AUTHENTICATION EXCEPTIONS (401)
# ═══════════════════════════════════════════════════════════

class UnauthorizedException(AppException):
    """Raised when authentication is required but not provided or invalid."""

    status_code = 401
    error_code = ErrorCodes.UNAUTHORIZED
    message = "Authentication required"


class InvalidCredentialsException(AppException):
    """Raised when login credentials are incorrect."""

    status_code = 401
    error_code = ErrorCodes.INVALID_CREDENTIALS
    message = "Invalid username or password"


class TokenExpiredException(AppException):
    """Raised when JWT token has expired."""

    status_code = 401
    error_code = ErrorCodes.TOKEN_EXPIRED
    message = "Token has expired"


class TokenInvalidException(AppException):
    """Raised when JWT token is invalid or malformed."""

    status_code = 401
    error_code = ErrorCodes.TOKEN_INVALID
    message = "Invalid token"


class SessionExpiredException(AppException):
    """Raised when user session has expired."""

    status_code = 401
    error_code = ErrorCodes.SESSION_EXPIRED
    message = "Session has expired"


class SessionRevokedException(AppException):
    """Raised when user session has been revoked."""

    status_code = 401
    error_code = ErrorCodes.SESSION_REVOKED
    message = "Session has been revoked"


# ═══════════════════════════════════════════════════════════
# AUTHORIZATION EXCEPTIONS (403)
# ═══════════════════════════════════════════════════════════

class ForbiddenException(AppException):
    """Raised when user doesn't have permission for an action."""

    status_code = 403
    error_code = ErrorCodes.FORBIDDEN
    message = "Access forbidden"


class InsufficientPermissionsException(AppException):
    """Raised when user lacks required role or permissions."""

    status_code = 403
    error_code = ErrorCodes.INSUFFICIENT_PERMISSIONS
    message = "Insufficient permissions for this action"


# ═══════════════════════════════════════════════════════════
# VALIDATION EXCEPTIONS (400)
# ═══════════════════════════════════════════════════════════

class ValidationException(AppException):
    """Raised when request data fails validation."""

    status_code = 400
    error_code = ErrorCodes.VALIDATION_ERROR
    message = "Validation error"


class InvalidInputException(AppException):
    """Raised when input data is invalid."""

    status_code = 400
    error_code = ErrorCodes.INVALID_INPUT
    message = "Invalid input"


# ═══════════════════════════════════════════════════════════
# RESOURCE EXCEPTIONS (404, 409)
# ═══════════════════════════════════════════════════════════

class NotFoundException(AppException):
    """Raised when a requested resource is not found."""

    status_code = 404
    error_code = ErrorCodes.NOT_FOUND
    message = "Resource not found"


class AlreadyExistsException(AppException):
    """Raised when trying to create a resource that already exists."""

    status_code = 409
    error_code = ErrorCodes.ALREADY_EXISTS
    message = "Resource already exists"


class ConflictException(AppException):
    """Raised when there's a conflict with the current state."""

    status_code = 409
    error_code = ErrorCodes.CONFLICT
    message = "Conflict with current state"


# ═══════════════════════════════════════════════════════════
# TWO-FACTOR AUTHENTICATION EXCEPTIONS
# ═══════════════════════════════════════════════════════════

class TwoFactorRequiredException(AppException):
    """Raised when 2FA verification is required to complete login."""

    status_code = 401
    error_code = ErrorCodes.TWO_FACTOR_REQUIRED
    message = "Two-factor authentication required"


class TwoFactorInvalidException(AppException):
    """Raised when 2FA code is invalid."""

    status_code = 401
    error_code = ErrorCodes.TWO_FACTOR_INVALID
    message = "Invalid two-factor authentication code"


class TwoFactorNotEnabledException(AppException):
    """Raised when 2FA operation requires 2FA to be enabled."""

    status_code = 400
    error_code = ErrorCodes.TWO_FACTOR_NOT_ENABLED
    message = "Two-factor authentication is not enabled"


# ═══════════════════════════════════════════════════════════
# ACCOUNT EXCEPTIONS
# ═══════════════════════════════════════════════════════════

class AccountLockedException(AppException):
    """Raised when account is locked due to too many failed attempts."""

    status_code = 403
    error_code = ErrorCodes.ACCOUNT_LOCKED
    message = "Account is temporarily locked"


class AccountDisabledException(AppException):
    """Raised when account has been disabled."""

    status_code = 403
    error_code = ErrorCodes.ACCOUNT_DISABLED
    message = "Account has been disabled"


# ═══════════════════════════════════════════════════════════
# RATE LIMITING EXCEPTIONS (429)
# ═══════════════════════════════════════════════════════════

class RateLimitExceededException(AppException):
    """Raised when rate limit has been exceeded."""

    status_code = 429
    error_code = ErrorCodes.RATE_LIMIT_EXCEEDED
    message = "Rate limit exceeded. Please try again later."


# ═══════════════════════════════════════════════════════════
# SERVER EXCEPTIONS (500, 503)
# ═══════════════════════════════════════════════════════════

class InternalErrorException(AppException):
    """Raised for unexpected internal errors."""

    status_code = 500
    error_code = ErrorCodes.INTERNAL_ERROR
    message = "An internal error occurred"


class DatabaseErrorException(AppException):
    """Raised when a database operation fails."""

    status_code = 500
    error_code = ErrorCodes.DATABASE_ERROR
    message = "Database error occurred"


class ServiceUnavailableException(AppException):
    """Raised when a required service is unavailable."""

    status_code = 503
    error_code = ErrorCodes.SERVICE_UNAVAILABLE
    message = "Service temporarily unavailable"
