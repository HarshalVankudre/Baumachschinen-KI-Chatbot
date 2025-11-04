"""
Authentication Dependencies

FastAPI dependencies for route protection and user authentication:
- get_current_user: Requires valid session
- require_superuser: Requires superuser or admin
- require_admin: Requires admin only
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, Request, status

from app.core.database import get_database
from app.core.session import validate_session
from app.models.user import UserModel

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> UserModel:
    """
    Get current authenticated user from session

    Args:
        request: FastAPI Request object

    Returns:
        UserModel if authenticated

    Raises:
        HTTPException 401 if not authenticated
        HTTPException 403 if account not active

    Usage:
        @router.get("/protected")
        async def protected_route(user: UserModel = Depends(get_current_user)):
            return {"user_id": user.user_id}
    """
    # Validate session and get user_id
    user_id = await validate_session(request)

    if not user_id:
        # Log authentication failure with request details
        logger.warning(
            f"Authentication failed - No valid session for {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
            headers={"WWW-Authenticate": "Cookie"},
        )

    # Load user from database
    db = get_database()
    user_doc = await db.users.find_one({"user_id": user_id})

    if not user_doc:
        logger.error(
            f"User {user_id} from valid session not found in database - "
            f"Session exists but user was deleted"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found. Please contact support.",
        )

    # Convert to UserModel
    user = UserModel(**user_doc)

    # Check account status
    if user.account_status != "active":
        status_messages = {
            "pending_verification": "Please verify your email address before logging in.",
            "pending_approval": "Your account is pending admin approval.",
            "rejected": "Your account registration was not approved.",
            "suspended": "Your account has been suspended. Please contact support.",
        }
        message = status_messages.get(user.account_status, "Your account is not active.")

        logger.warning(
            f"Access denied for user {user.username} - "
            f"Account status: {user.account_status}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
        )

    logger.debug(
        f"Authenticated user: {user.username} ({user.authorization_level}) "
        f"accessing {request.url.path}"
    )
    return user


async def require_superuser(
    user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    Require user to be superuser or admin

    Args:
        user: Current authenticated user

    Returns:
        UserModel if superuser or admin

    Raises:
        HTTPException 403 if not superuser/admin

    Usage:
        @router.post("/admin-action")
        async def admin_only(user: UserModel = Depends(require_superuser)):
            return {"admin": user.username}
    """
    if user.authorization_level not in ["superuser", "admin"]:
        logger.warning(
            f"User {user.username} attempted to access superuser-only resource"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires superuser or admin privileges.",
        )

    return user


async def require_admin(
    user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    Require user to be admin

    Args:
        user: Current authenticated user

    Returns:
        UserModel if admin

    Raises:
        HTTPException 403 if not admin

    Usage:
        @router.get("/admin/users")
        async def list_users(user: UserModel = Depends(require_admin)):
            return {"admin": user.username}
    """
    if user.authorization_level != "admin":
        logger.warning(
            f"User {user.username} attempted to access admin-only resource"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires admin privileges.",
        )

    return user


async def get_current_user_optional(request: Request) -> Optional[UserModel]:
    """
    Get current user if authenticated, None otherwise

    Args:
        request: FastAPI Request object

    Returns:
        UserModel if authenticated, None otherwise

    Usage:
        Used for endpoints that work differently for authenticated users
        but are also accessible to unauthenticated users
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        return None
