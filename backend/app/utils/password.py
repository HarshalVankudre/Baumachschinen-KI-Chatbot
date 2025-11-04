"""
Password Utilities Module

Provides password hashing, verification, and strength validation functions.
Uses Argon2 for secure password hashing (OWASP recommended).

This module extracts password-specific functionality from app.utils.security
to provide a focused interface for password operations.
"""

from app.utils.security import (
    hash_password as _hash_password,
    verify_password as _verify_password,
    validate_password_strength as _validate_password_strength,
)


def hash_password(plain_password: str) -> str:
    """
    Hash a password using Argon2.

    Args:
        plain_password: Plain text password to hash

    Returns:
        Hashed password string with embedded salt and parameters

    Raises:
        ValueError: If password is empty or None
        Exception: If hashing fails

    Example:
        >>> hashed = hash_password("MySecureP@ssw0rd")
        >>> assert hashed.startswith("$argon2")
    """
    if not plain_password:
        raise ValueError("Password cannot be empty")

    return _hash_password(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored password hash

    Returns:
        True if password matches, False otherwise

    Raises:
        ValueError: If hashed_password is empty or None

    Example:
        >>> hashed = hash_password("MyPassword123!")
        >>> assert verify_password("MyPassword123!", hashed) is True
        >>> assert verify_password("WrongPassword", hashed) is False
    """
    if not hashed_password:
        raise ValueError("Hashed password cannot be empty")

    return _verify_password(plain_password, hashed_password)


def validate_password_strength(password: str) -> dict:
    """
    Validate password strength against security requirements.

    Requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Args:
        password: Password to validate

    Returns:
        Dictionary with validation results:
        {
            "valid": bool,
            "errors": list of error messages (empty if valid)
        }

    Example:
        >>> result = validate_password_strength("Weak")
        >>> assert result["valid"] is False
        >>> assert len(result["errors"]) > 0

        >>> result = validate_password_strength("SecureP@ssw0rd123")
        >>> assert result["valid"] is True
        >>> assert len(result["errors"]) == 0
    """
    is_valid, error_message = _validate_password_strength(password)

    if is_valid:
        return {"valid": True, "errors": []}
    else:
        # Collect all errors by checking all requirements
        errors = []

        if len(password) < 12:
            errors.append("Password must be at least 12 characters long")

        import re
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\/'`~;]", password):
            errors.append("Password must contain at least one special character")

        return {"valid": False, "errors": errors}
