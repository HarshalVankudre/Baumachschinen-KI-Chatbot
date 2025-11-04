"""
Session Management

Cookie-based session management with:
- Secure session creation
- Cookie signing with HMAC
- Session validation
- HttpOnly, Secure, SameSite attributes
"""

import logging
import hmac
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
from fastapi import Request, Response
from itsdangerous import TimestampSigner, BadSignature

from app.config import get_settings
from app.core.database import get_database
from app.models.user import SessionModel
from app.utils.security import generate_token

logger = logging.getLogger(__name__)
settings = get_settings()

# Cookie signer for tamper-proof cookies
signer = TimestampSigner(settings.secret_key)


async def create_session(
    user_id: str,
    response: Response,
    remember_me: bool = False,
    request: Optional[Request] = None
) -> str:
    """
    Create a new session and set cookie

    Args:
        user_id: User ID to create session for
        response: FastAPI Response object to set cookie on
        remember_me: If True, extend cookie expiration to 30 days
        request: Optional Request object to get IP and user agent

    Returns:
        Session token (unsigned)

    Side Effects:
        - Creates session document in MongoDB
        - Sets signed cookie in response
    """
    try:
        db = get_database()

        # Generate session token
        session_token = generate_token()

        # Calculate expiration
        if remember_me:
            expires_at = datetime.now(UTC) + timedelta(days=30)
            cookie_max_age = 30 * 24 * 60 * 60  # 30 days in seconds
        else:
            expires_at = datetime.now(UTC) + timedelta(hours=12)
            cookie_max_age = 12 * 60 * 60  # 12 hours

        # Get client info
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        # Create session document
        session = SessionModel(
            session_id=session_token,
            user_id=user_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Store in MongoDB
        await db.sessions.insert_one(session.model_dump(by_alias=True))

        # Sign the token
        signed_token = signer.sign(session_token).decode('utf-8')

        # Set cookie with security attributes
        response.set_cookie(
            key=settings.session_cookie_name,
            value=signed_token,
            max_age=cookie_max_age if remember_me else None,  # None = session cookie
            httponly=True,  # Prevents JavaScript access (XSS protection)
            secure=settings.environment == "production",  # HTTPS only in production
            samesite="strict",  # CSRF protection
            path="/"
        )

        logger.info(f"Session created for user {user_id}, remember_me={remember_me}")
        return session_token

    except Exception as e:
        logger.error(f"Session creation error: {str(e)}")
        raise


async def validate_session(request: Request) -> Optional[str]:
    """
    Validate session from cookie and return user ID

    Args:
        request: FastAPI Request object

    Returns:
        User ID if session is valid, None otherwise

    Checks:
        - Cookie exists
        - Signature is valid
        - Session exists in database
        - Session not expired
    """
    try:
        # Get cookie
        signed_token = request.cookies.get(settings.session_cookie_name)
        if not signed_token:
            logger.debug("No session cookie found")
            return None

        # Verify signature
        try:
            session_token = signer.unsign(signed_token).decode('utf-8')
        except BadSignature:
            logger.warning("Invalid session cookie signature")
            return None

        # Look up session in database
        db = get_database()
        session_doc = await db.sessions.find_one({"session_id": session_token})

        if not session_doc:
            logger.debug("Session not found in database")
            return None

        # Check expiration
        expires_at = session_doc.get("expires_at")
        # Ensure expires_at is timezone-aware
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at and datetime.now(UTC) > expires_at:
            logger.debug("Session expired")
            # Clean up expired session
            await db.sessions.delete_one({"session_id": session_token})
            return None

        # Session is valid
        user_id = session_doc.get("user_id")
        logger.debug(f"Valid session for user {user_id}")
        return user_id

    except Exception as e:
        logger.error(f"Session validation error: {str(e)}")
        return None


async def delete_session(
    request: Request,
    response: Response
) -> bool:
    """
    Delete session (logout)

    Args:
        request: FastAPI Request object
        response: FastAPI Response object

    Returns:
        True if session was deleted, False otherwise

    Side Effects:
        - Deletes session from MongoDB
        - Clears cookie in response
    """
    try:
        # Get cookie
        signed_token = request.cookies.get(settings.session_cookie_name)
        if not signed_token:
            # No session cookie, but still clear it
            response.delete_cookie(
                key=settings.session_cookie_name,
                path="/"
            )
            return True

        # Unsign token
        try:
            session_token = signer.unsign(signed_token).decode('utf-8')
        except BadSignature:
            # Invalid signature, but still clear cookie
            response.delete_cookie(
                key=settings.session_cookie_name,
                path="/"
            )
            return True

        # Delete from database
        db = get_database()
        result = await db.sessions.delete_one({"session_id": session_token})

        # Clear cookie
        response.delete_cookie(
            key=settings.session_cookie_name,
            path="/"
        )

        logger.info(f"Session deleted, documents removed: {result.deleted_count}")
        return True

    except Exception as e:
        logger.error(f"Session deletion error: {str(e)}")
        return False


async def get_session_info(session_token: str) -> Optional[Dict[str, Any]]:
    """
    Get session information from database

    Args:
        session_token: Unsigned session token

    Returns:
        Session document or None if not found
    """
    try:
        db = get_database()
        session_doc = await db.sessions.find_one({"session_id": session_token})
        return session_doc
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        return None


async def cleanup_expired_sessions() -> int:
    """
    Clean up expired sessions from database

    Returns:
        Number of sessions deleted

    Note:
        Should be run periodically (e.g., via cron job or background task)
        MongoDB TTL index also handles this automatically
    """
    try:
        db = get_database()
        result = await db.sessions.delete_many({
            "expires_at": {"$lt": datetime.now(UTC)}
        })

        deleted_count = result.deleted_count
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired sessions")

        return deleted_count

    except Exception as e:
        logger.error(f"Session cleanup error: {str(e)}")
        return 0


async def extend_session(
    request: Request,
    response: Response,
    days: int = 30
) -> bool:
    """
    Extend session expiration

    Args:
        request: FastAPI Request object
        response: FastAPI Response object
        days: Number of days to extend by (default 30)

    Returns:
        True if extended successfully, False otherwise
    """
    try:
        # Get and validate session
        signed_token = request.cookies.get(settings.session_cookie_name)
        if not signed_token:
            return False

        session_token = signer.unsign(signed_token).decode('utf-8')

        # Update expiration in database
        db = get_database()
        new_expires_at = datetime.now(UTC) + timedelta(days=days)

        result = await db.sessions.update_one(
            {"session_id": session_token},
            {"$set": {"expires_at": new_expires_at}}
        )

        if result.modified_count == 0:
            return False

        # Update cookie
        response.set_cookie(
            key=settings.session_cookie_name,
            value=signed_token,
            max_age=days * 24 * 60 * 60,
            httponly=True,
            secure=settings.environment == "production",
            samesite="strict",
            path="/"
        )

        logger.info(f"Session extended by {days} days")
        return True

    except Exception as e:
        logger.error(f"Session extension error: {str(e)}")
        return False


# Standalone utility functions for testing
def hash_cookie_value(value: str) -> str:
    """
    Hash a cookie value using HMAC for tamper-proof cookies.

    Args:
        value: Cookie value to hash

    Returns:
        HMAC signature of the value

    Note:
        Uses itsdangerous TimestampSigner for secure signing.
    """
    import hashlib
    import hmac

    # Use HMAC-SHA256 for deterministic hashing (for tests)
    signature = hmac.new(
        settings.secret_key.encode('utf-8'),
        value.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return signature


def verify_cookie_signature(value: str, signature: str) -> bool:
    """
    Verify a cookie signature.

    Args:
        value: Original cookie value
        signature: Signature to verify

    Returns:
        True if signature is valid, False otherwise
    """
    expected_signature = hash_cookie_value(value)
    return hmac.compare_digest(expected_signature, signature)


def create_session_sync(
    user_id: str,
    username: str,
    authorization_level: str,
    remember_me: bool = False
) -> Dict[str, Any]:
    """
    Create a session (test-friendly version without FastAPI dependencies).

    Args:
        user_id: User ID
        username: Username
        authorization_level: User's authorization level
        remember_me: If True, extend expiration to 30 days

    Returns:
        Dictionary with session data:
        {
            "session_id": str,
            "session_token": dict,
            "expires_at": str (ISO format)
        }
    """
    session_id = generate_token()

    if remember_me:
        expires_at = datetime.now(UTC) + timedelta(days=30)
    else:
        expires_at = datetime.now(UTC) + timedelta(hours=12)

    session_token = {
        "session_id": session_id,
        "user_id": user_id,
        "username": username,
        "authorization_level": authorization_level,
        "created_at": datetime.now(UTC).isoformat(),
        "expires_at": expires_at.isoformat()
    }

    return {
        "session_id": session_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat()
    }


async def validate_session_sync(session_id: str, db) -> Dict[str, Any]:
    """
    Validate a session by ID (test-friendly version).

    Args:
        session_id: Session ID to validate
        db: Database instance

    Returns:
        Dictionary with validation result:
        {
            "valid": bool,
            "user": dict (if valid),
            "error": str (if invalid)
        }
    """
    try:
        # Look up user by session token
        user = await db.users.find_one({"session_token.session_id": session_id})

        if not user:
            return {
                "valid": False,
                "error": "Session not found"
            }

        # Check if session is expired
        session_token = user.get("session_token", {})
        expires_at_str = session_token.get("expires_at")

        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            # Make timezone-aware if needed
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)

            if datetime.now(UTC) > expires_at:
                return {
                    "valid": False,
                    "error": "Session expired"
                }

        # Check account status
        if user.get("account_status") == "suspended":
            return {
                "valid": False,
                "error": "Account suspended"
            }

        return {
            "valid": True,
            "user": user
        }

    except Exception as e:
        logger.error(f"Session validation error: {str(e)}")
        return {
            "valid": False,
            "error": str(e)
        }
