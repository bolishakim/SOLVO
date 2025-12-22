"""
Validation Utilities

Common validation functions for user input.
"""

import re
from typing import Any


# ═══════════════════════════════════════════════════════════
# EMAIL VALIDATION
# ═══════════════════════════════════════════════════════════

# RFC 5322 compliant email regex (simplified)
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


def validate_email(email: str) -> tuple[bool, str | None]:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        valid, error = validate_email("user@example.com")
        if not valid:
            raise ValidationException(message=error)
    """
    if not email:
        return False, "Email is required"

    if len(email) > 255:
        return False, "Email must be 255 characters or less"

    if not EMAIL_REGEX.match(email):
        return False, "Invalid email format"

    return True, None


def is_valid_email(email: str) -> bool:
    """
    Check if email is valid (simple boolean check).

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    valid, _ = validate_email(email)
    return valid


# ═══════════════════════════════════════════════════════════
# PASSWORD VALIDATION
# ═══════════════════════════════════════════════════════════

def validate_password(
    password: str,
    min_length: int = 8,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digit: bool = True,
    require_special: bool = False,
) -> tuple[bool, str | None]:
    """
    Validate password strength.

    Args:
        password: Password to validate
        min_length: Minimum password length (default: 8)
        require_uppercase: Require at least one uppercase letter
        require_lowercase: Require at least one lowercase letter
        require_digit: Require at least one digit
        require_special: Require at least one special character

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        valid, error = validate_password("MyPass123!")
        if not valid:
            raise ValidationException(message=error)
    """
    if not password:
        return False, "Password is required"

    errors = []

    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters")

    if require_uppercase and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if require_lowercase and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if require_digit and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    if require_special:
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append("Password must contain at least one special character")

    if errors:
        return False, "; ".join(errors)

    return True, None


def is_valid_password(password: str) -> bool:
    """
    Check if password meets strength requirements (simple boolean check).

    Args:
        password: Password to validate

    Returns:
        True if valid, False otherwise
    """
    valid, _ = validate_password(password)
    return valid


def get_password_strength(password: str) -> dict[str, Any]:
    """
    Analyze password strength and return detailed feedback.

    Args:
        password: Password to analyze

    Returns:
        Dictionary with strength score and details
    """
    score = 0
    feedback = []

    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Use at least 8 characters")

    if len(password) >= 12:
        score += 1

    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append("Add uppercase letters")

    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append("Add lowercase letters")

    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append("Add numbers")

    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if any(c in special_chars for c in password):
        score += 1
    else:
        feedback.append("Add special characters")

    # Determine strength level
    if score <= 2:
        strength = "weak"
    elif score <= 4:
        strength = "medium"
    else:
        strength = "strong"

    return {
        "score": score,
        "max_score": 6,
        "strength": strength,
        "feedback": feedback,
    }


# ═══════════════════════════════════════════════════════════
# USERNAME VALIDATION
# ═══════════════════════════════════════════════════════════

# Username: alphanumeric, underscore, hyphen, 3-50 chars
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,50}$")


def validate_username(username: str) -> tuple[bool, str | None]:
    """
    Validate username format.

    Args:
        username: Username to validate

    Returns:
        Tuple of (is_valid, error_message)

    Rules:
        - 3-50 characters
        - Only alphanumeric, underscore, and hyphen
        - Must start with a letter

    Example:
        valid, error = validate_username("john_doe")
        if not valid:
            raise ValidationException(message=error)
    """
    if not username:
        return False, "Username is required"

    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 50:
        return False, "Username must be 50 characters or less"

    if not username[0].isalpha():
        return False, "Username must start with a letter"

    if not USERNAME_REGEX.match(username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"

    return True, None


def is_valid_username(username: str) -> bool:
    """
    Check if username is valid (simple boolean check).

    Args:
        username: Username to validate

    Returns:
        True if valid, False otherwise
    """
    valid, _ = validate_username(username)
    return valid


# ═══════════════════════════════════════════════════════════
# PHONE NUMBER VALIDATION
# ═══════════════════════════════════════════════════════════

# Basic phone regex: digits, spaces, hyphens, parentheses, plus sign
PHONE_REGEX = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")


def validate_phone_number(phone: str | None) -> tuple[bool, str | None]:
    """
    Validate phone number format (optional field).

    Args:
        phone: Phone number to validate (can be None)

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        valid, error = validate_phone_number("+43 123 456 7890")
    """
    if not phone:
        return True, None  # Optional field

    # Remove whitespace for length check
    cleaned = re.sub(r"\s", "", phone)

    if len(cleaned) < 7:
        return False, "Phone number too short"

    if len(cleaned) > 20:
        return False, "Phone number too long"

    if not PHONE_REGEX.match(phone):
        return False, "Invalid phone number format"

    return True, None


# ═══════════════════════════════════════════════════════════
# NAME VALIDATION
# ═══════════════════════════════════════════════════════════

def validate_name(name: str, field_name: str = "Name") -> tuple[bool, str | None]:
    """
    Validate a name field (first name, last name, etc.).

    Args:
        name: Name to validate
        field_name: Name of the field for error messages

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        valid, error = validate_name("John", "First name")
    """
    if not name:
        return False, f"{field_name} is required"

    if len(name) < 1:
        return False, f"{field_name} must be at least 1 character"

    if len(name) > 100:
        return False, f"{field_name} must be 100 characters or less"

    # Allow letters, spaces, hyphens, apostrophes (for names like O'Brien)
    if not re.match(r"^[a-zA-ZÀ-ÿ\s\-']+$", name):
        return False, f"{field_name} contains invalid characters"

    return True, None


# ═══════════════════════════════════════════════════════════
# COMBINED VALIDATION
# ═══════════════════════════════════════════════════════════

def validate_registration_data(
    username: str,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    phone_number: str | None = None,
) -> tuple[bool, dict[str, str]]:
    """
    Validate all registration fields at once.

    Args:
        username: Username
        email: Email address
        password: Password
        first_name: First name
        last_name: Last name
        phone_number: Optional phone number

    Returns:
        Tuple of (all_valid, errors_dict)

    Example:
        valid, errors = validate_registration_data(
            username="john_doe",
            email="john@example.com",
            password="SecurePass123",
            first_name="John",
            last_name="Doe",
        )
        if not valid:
            raise ValidationException(details={"fields": errors})
    """
    errors = {}

    valid, error = validate_username(username)
    if not valid:
        errors["username"] = error

    valid, error = validate_email(email)
    if not valid:
        errors["email"] = error

    valid, error = validate_password(password)
    if not valid:
        errors["password"] = error

    valid, error = validate_name(first_name, "First name")
    if not valid:
        errors["first_name"] = error

    valid, error = validate_name(last_name, "Last name")
    if not valid:
        errors["last_name"] = error

    if phone_number:
        valid, error = validate_phone_number(phone_number)
        if not valid:
            errors["phone_number"] = error

    return len(errors) == 0, errors
