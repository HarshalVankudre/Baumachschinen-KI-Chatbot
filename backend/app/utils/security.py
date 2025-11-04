"""
Security Utilities

Password hashing, validation, and token generation utilities.
Uses Argon2 for password hashing (OWASP recommended).
"""

import logging
import re
import uuid
from typing import Tuple
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash

logger = logging.getLogger(__name__)

# Initialize Argon2 password hasher with OWASP recommended parameters
ph = PasswordHasher(
    time_cost=2,           # Number of iterations
    memory_cost=65536,     # Memory usage in KiB (64 MB)
    parallelism=4,         # Number of parallel threads
    hash_len=32,           # Length of hash in bytes
    salt_len=16            # Length of salt in bytes
)


def hash_password(plain_password: str) -> str:
    """
    Hash a password using Argon2

    Args:
        plain_password: Plain text password to hash

    Returns:
        Hashed password string

    Note:
        The hash includes the salt and parameters, so no separate storage needed
    """
    try:
        hashed = ph.hash(plain_password)
        logger.debug("Password hashed successfully")
        return hashed
    except Exception as e:
        logger.error(f"Password hashing error: {str(e)}")
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored password hash

    Returns:
        True if password matches, False otherwise
    """
    try:
        ph.verify(hashed_password, plain_password)

        # Check if rehashing is needed (parameters changed)
        if ph.check_needs_rehash(hashed_password):
            logger.info("Password hash needs rehashing with new parameters")
            # Note: Caller should rehash and update database

        return True

    except (VerifyMismatchError, InvalidHash):
        logger.debug("Password verification failed")
        return False
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength according to security requirements

    Requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid
        - (False, "error message") if invalid
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\/'`~;]", password):
        return False, "Password must contain at least one special character"

    return True, ""


def generate_token() -> str:
    """
    Generate a secure random token

    Returns:
        UUID4 token as string

    Note:
        Used for email verification tokens, session tokens, etc.
    """
    return str(uuid.uuid4())


def validate_email(email: str) -> bool:
    """
    Validate email format

    Args:
        email: Email address to validate

    Returns:
        True if valid email format, False otherwise
    """
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
