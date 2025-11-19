"""
Authentication Endpoints

Handles user authentication and authorization:
- User registration (POST /api/auth/register)
- Email verification (POST /api/auth/verify-email)
- Login (POST /api/auth/login)
- Logout (POST /api/auth/logout)
- Get current user (GET /api/auth/me)
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Request, Response, Depends
from pydantic import BaseModel

from app.core.database import get_database
from app.core.session import create_session, delete_session, validate_session
from app.models.user import UserModel
from app.models.audit_log import AuditLogModel
from app.schemas.auth import (
    UserRegistration,
    UserLogin,
    UserResponse,
    EmailVerificationRequest,
    PasswordResetRequest,
    PasswordResetTokenVerification,
    PasswordResetConfirm,
)
from app.services.email_service import get_email_service
from app.utils.security import (
    hash_password,
    verify_password,
    generate_token,
)
from app.api.v1.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    user_id: Optional[str] = None


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=MessageResponse)
async def register(
    registration_data: UserRegistration,
    request: Request
) -> MessageResponse:
    """
    Register a new user account

    Process:
    1. Validate registration data
    2. Check username and email uniqueness
    3. Hash password with Argon2
    4. Create user document with status 'pending_verification'
    5. Send verification email
    6. Return success response

    After successful registration:
    - User must verify email (BE-011)
    - Admin must approve account (BE-028)
    - Then user can log in (BE-012)
    """
    try:
        db = get_database()

        # Check if passwords match
        if registration_data.password != registration_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )

        # Check username uniqueness
        existing_user = await db.users.find_one({"username": registration_data.username.lower()})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists"
            )

        # Check email uniqueness
        existing_email = await db.users.find_one({"email": registration_data.email.lower()})
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        # Hash password
        password_hash = hash_password(registration_data.password)

        # Generate user ID and email verification token
        user_id = generate_token()
        verification_token = generate_token()
        verification_expires = datetime.now(UTC) + timedelta(hours=24)

        # Create user document
        user = UserModel(
            user_id=user_id,
            username=registration_data.username.lower(),
            email=registration_data.email.lower(),
            password_hash=password_hash,
            email_verification_token=verification_token,
            email_verification_expires=verification_expires,
            account_status="pending_verification",
            email_verified=False,
            authorization_level="regular",  # Default, will be set by admin on approval
        )

        # Insert into database
        await db.users.insert_one(user.model_dump(by_alias=True))
        logger.info(f"User registered: {user.username} ({user.user_id})")

        # Send verification email
        email_service = get_email_service()
        email_sent = await email_service.send_verification_email(
            email=user.email,
            username=user.username,
            verification_token=verification_token
        )

        if not email_sent:
            logger.warning(f"Failed to send verification email to {user.email}")
            # Don't fail registration if email fails
            # User can request resend later
        else:
            logger.info(f"Verification email sent successfully to {user.email}")

        return MessageResponse(
            message="Registration successful. Please check your email to verify your account.",
            user_id=user.user_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration. Please try again."
        )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verification_data: EmailVerificationRequest
) -> MessageResponse:
    """
    Verify user email address

    Process:
    1. Validate verification token
    2. Check token expiration (24 hours)
    3. Update user: email_verified=true, account_status='pending_approval'
    4. Send notification to admin
    5. Return success response

    After email verification:
    - User status changes to 'pending_approval'
    - Admin receives notification (BE-027)
    - Admin must approve before user can log in (BE-028)
    """
    try:
        db = get_database()

        # Find user by verification token
        user_doc = await db.users.find_one({
            "email_verification_token": verification_data.token
        })

        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid verification token"
            )

        user = UserModel(**user_doc)

        # Check if already verified
        if user.email_verified:
            return MessageResponse(
                message="Email already verified. Please wait for admin approval."
            )

        # Check token expiration
        expires = user.email_verification_expires
        if expires:
            # Make timezone-aware if naive (MongoDB returns naive datetimes)
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=UTC)
        if expires and datetime.now(UTC) > expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired. Please request a new one."
            )

        # Update user
        await db.users.update_one(
            {"user_id": user.user_id},
            {
                "$set": {
                    "email_verified": True,
                    "account_status": "pending_approval",
                    "email_verification_token": None,
                    "email_verification_expires": None,
                }
            }
        )

        logger.info(f"Email verified for user: {user.username}")

        # Send notification to admin
        email_service = get_email_service()
        admin_notification_sent = await email_service.send_admin_notification({
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at
        })

        if not admin_notification_sent:
            logger.warning(f"Failed to send admin notification for user: {user.email}")
        else:
            logger.info(f"Admin notification sent for user: {user.email}")

        # Send verification success email to user
        verification_success_sent = await email_service.send_verification_success_email(
            email=user.email,
            username=user.username
        )

        if not verification_success_sent:
            logger.warning(f"Failed to send verification success email to {user.email}")
        else:
            logger.info(f"Verification success email sent successfully to {user.email}")

        return MessageResponse(
            message="Email verified successfully! Your account is pending admin approval."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during email verification."
        )


@router.post("/login", response_model=UserResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    response: Response
) -> UserResponse:
    """
    User login

    Process:
    1. Find user by username (or email)
    2. Verify password with Argon2
    3. Check account status (must be 'active')
    4. Create session and set cookie
    5. Update last_login timestamp
    6. Create audit log entry
    7. Return user data

    Security features:
    - Generic error message (don't reveal if username exists)
    - Password verification with Argon2
    - HttpOnly, Secure, SameSite cookies
    - Failed login attempt logging
    """
    try:
        db = get_database()

        # Find user by username or email
        user_doc = await db.users.find_one({
            "$or": [
                {"username": login_data.username.lower()},
                {"email": login_data.username.lower()}
            ]
        })

        # Generic error message for security
        invalid_credentials_error = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

        if not user_doc:
            logger.warning(f"Login attempt with non-existent username: {login_data.username}")
            raise invalid_credentials_error

        user = UserModel(**user_doc)

        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            logger.warning(f"Failed login attempt for user: {user.username}")
            raise invalid_credentials_error

        # Check account status
        if user.account_status != "active":
            status_messages = {
                "pending_verification": "Please verify your email address before logging in.",
                "pending_approval": "Your account is pending admin approval. You will be notified when approved.",
                "rejected": "Your account registration was not approved. Please contact support.",
                "suspended": "Your account has been suspended. Please contact support.",
            }
            message = status_messages.get(user.account_status, "Your account is not active.")

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=message
            )

        # Create session
        session_token = await create_session(
            user_id=user.user_id,
            response=response,
            remember_me=login_data.remember_me,
            request=request
        )

        # Update last login
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": {"last_login": datetime.now(UTC)}}
        )

        # Create audit log
        audit_log = AuditLogModel(
            log_id=generate_token(),
            action_type="user_login",
            admin_user_id=None,  # Self-action
            target_user_id=user.user_id,
            target_username=user.username,
            details={
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "remember_me": login_data.remember_me
            }
        )
        await db.audit_logs.insert_one(audit_log.model_dump(by_alias=True))

        logger.info(f"Successful login: {user.username}")

        # Return user data
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            authorization_level=user.authorization_level,
            account_status=user.account_status,
            email_verified=user.email_verified,
            created_at=user.created_at,
            last_login=datetime.now(UTC)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login."
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response
) -> MessageResponse:
    """
    User logout

    Process:
    1. Validate session from cookie
    2. Delete session from database
    3. Clear cookie
    4. Create audit log entry
    5. Return success response

    Features:
    - Idempotent (safe to call multiple times)
    - Always returns success (even if no session)
    - Clears cookie in all cases
    """
    try:
        # Try to get user info before deleting session
        user_id = await validate_session(request)
        username = None

        if user_id:
            db = get_database()
            user_doc = await db.users.find_one({"user_id": user_id})
            if user_doc:
                username = user_doc.get("username")

                # Create audit log
                audit_log = AuditLogModel(
            log_id=generate_token(),
            action_type="user_logout",
                    admin_user_id=None,
                    target_user_id=user_id,
                    target_username=username,
                    details={
                        "ip_address": request.client.host if request.client else None
                    }
                )
                await db.audit_logs.insert_one(audit_log.model_dump(by_alias=True))

        # Delete session (handles all cleanup)
        await delete_session(request, response)

        logger.info(f"User logged out: {username or 'unknown'}")

        return MessageResponse(message="Logged out successfully")

    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        # Still clear the cookie even if there's an error
        response.delete_cookie(key="session_id", path="/")
        return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: UserModel = Depends(get_current_user)
) -> UserResponse:
    """
    Get current user information

    Requires authentication via session cookie.

    Used by frontend to:
    - Check authentication status on app initialization
    - Restore user state after page reload
    - Display user information in UI

    Returns:
        UserResponse with current user data
    """
    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        authorization_level=user.authorization_level,
        account_status=user.account_status,
        email_verified=user.email_verified,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    request: Request
) -> MessageResponse:
    """
    Request password reset email

    Security features:
    - Generic success message (don't reveal if email exists)
    - Rate limiting (max 3 requests per hour per email)
    - Secure token generation
    - Token expiration (1 hour)

    Process:
    1. Check rate limiting
    2. Find user by email (silently fail if not found)
    3. Generate secure reset token
    4. Save token with expiration
    5. Send reset email
    6. Return generic success message
    """
    try:
        db = get_database()

        # Always return the same message for security
        success_message = MessageResponse(
            message="Wenn ein Konto mit dieser E-Mail-Adresse existiert, wurde eine E-Mail mit Anweisungen zum Zurücksetzen des Passworts gesendet."
        )

        # Find user by email
        user_doc = await db.users.find_one({"email": reset_request.email.lower()})

        # If user doesn't exist, return success anyway (security: don't reveal)
        if not user_doc:
            logger.info(f"Password reset requested for non-existent email: {reset_request.email}")
            return success_message

        user = UserModel(**user_doc)

        # Check rate limiting (max 3 attempts per hour)
        now = datetime.now(UTC)
        reset_window_start = now - timedelta(hours=1)

        # Check if last attempt was within the hour window
        if user.password_reset_last_attempt:
            last_attempt = user.password_reset_last_attempt
            if last_attempt.tzinfo is None:
                last_attempt = last_attempt.replace(tzinfo=UTC)

            if last_attempt > reset_window_start:
                # Within the hour window, check attempt count
                if user.password_reset_attempts >= 3:
                    logger.warning(f"Rate limit exceeded for password reset: {user.email}")
                    # Still return success message (don't reveal rate limiting)
                    return success_message

                # Increment attempt count
                await db.users.update_one(
                    {"user_id": user.user_id},
                    {
                        "$inc": {"password_reset_attempts": 1},
                        "$set": {"password_reset_last_attempt": now}
                    }
                )
            else:
                # Outside window, reset counter
                await db.users.update_one(
                    {"user_id": user.user_id},
                    {
                        "$set": {
                            "password_reset_attempts": 1,
                            "password_reset_last_attempt": now
                        }
                    }
                )
        else:
            # First attempt
            await db.users.update_one(
                {"user_id": user.user_id},
                {
                    "$set": {
                        "password_reset_attempts": 1,
                        "password_reset_last_attempt": now
                    }
                }
            )

        # Generate secure reset token
        reset_token = generate_token()
        reset_expires = now + timedelta(hours=1)

        # Save token to user
        await db.users.update_one(
            {"user_id": user.user_id},
            {
                "$set": {
                    "password_reset_token": reset_token,
                    "password_reset_expires": reset_expires
                }
            }
        )

        # Send reset email
        email_service = get_email_service()
        email_sent = await email_service.send_password_reset_email(
            email=user.email,
            username=user.username,
            reset_token=reset_token
        )

        if not email_sent:
            logger.error(f"Failed to send password reset email to {user.email}")
            # Still return success (don't reveal email sending failed)

        # Log the password reset request
        audit_log = AuditLogModel(
            log_id=generate_token(),
            action_type="password_reset_requested",
            admin_user_id=None,
            target_user_id=user.user_id,
            target_username=user.username,
            details={
                "email": user.email,
                "ip_address": request.client.host if request.client else None
            }
        )
        await db.audit_logs.insert_one(audit_log.model_dump(by_alias=True))

        logger.info(f"Password reset requested for user: {user.username}")

        return success_message

    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}", exc_info=True)
        # Still return success message (don't reveal errors)
        return MessageResponse(
            message="Wenn ein Konto mit dieser E-Mail-Adresse existiert, wurde eine E-Mail mit Anweisungen zum Zurücksetzen des Passworts gesendet."
        )


@router.get("/reset-password/verify/{token}", response_model=MessageResponse)
async def verify_reset_token(token: str) -> MessageResponse:
    """
    Verify password reset token is valid and not expired

    Process:
    1. Find user by reset token
    2. Check token expiration
    3. Return validation result

    Used by frontend to validate token before showing reset form
    """
    try:
        db = get_database()

        # Find user by reset token
        user_doc = await db.users.find_one({"password_reset_token": token})

        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ungültiger oder abgelaufener Reset-Link"
            )

        user = UserModel(**user_doc)

        # Check token expiration
        expires = user.password_reset_expires
        if expires:
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=UTC)

        if not expires or datetime.now(UTC) > expires:
            # Token expired, clear it
            await db.users.update_one(
                {"user_id": user.user_id},
                {
                    "$set": {
                        "password_reset_token": None,
                        "password_reset_expires": None
                    }
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Der Reset-Link ist abgelaufen. Bitte fordern Sie einen neuen an."
            )

        return MessageResponse(
            message="Token ist gültig"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut."
        )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    request: Request
) -> MessageResponse:
    """
    Reset password with valid token

    Security features:
    - Token validation and expiration check
    - Password strength validation
    - Token single-use (invalidated after use)
    - Audit logging

    Process:
    1. Find user by reset token
    2. Verify token not expired
    3. Validate new password strength
    4. Hash new password
    5. Update user password
    6. Invalidate token (single use)
    7. Log password reset
    8. Send confirmation email (optional)
    """
    try:
        db = get_database()

        # Validate passwords match
        if reset_data.new_password != reset_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Die Passwörter stimmen nicht überein"
            )

        # Find user by reset token
        user_doc = await db.users.find_one({"password_reset_token": reset_data.token})

        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ungültiger oder bereits verwendeter Reset-Link"
            )

        user = UserModel(**user_doc)

        # Check token expiration
        expires = user.password_reset_expires
        if expires:
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=UTC)

        if not expires or datetime.now(UTC) > expires:
            # Token expired, clear it
            await db.users.update_one(
                {"user_id": user.user_id},
                {
                    "$set": {
                        "password_reset_token": None,
                        "password_reset_expires": None
                    }
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Der Reset-Link ist abgelaufen. Bitte fordern Sie einen neuen an."
            )

        # Hash the new password
        password_hash = hash_password(reset_data.new_password)

        # Update password and clear reset token (single use)
        await db.users.update_one(
            {"user_id": user.user_id},
            {
                "$set": {
                    "password_hash": password_hash,
                    "password_reset_token": None,
                    "password_reset_expires": None,
                    "password_reset_attempts": 0,
                    "password_reset_last_attempt": None
                }
            }
        )

        # Create audit log
        audit_log = AuditLogModel(
            log_id=generate_token(),
            action_type="password_reset_completed",
            admin_user_id=None,
            target_user_id=user.user_id,
            target_username=user.username,
            details={
                "ip_address": request.client.host if request.client else None,
                "reset_at": datetime.now(UTC).isoformat()
            }
        )
        await db.audit_logs.insert_one(audit_log.model_dump(by_alias=True))

        logger.info(f"Password reset completed for user: {user.username}")

        return MessageResponse(
            message="Ihr Passwort wurde erfolgreich zurückgesetzt. Sie können sich jetzt mit Ihrem neuen Passwort anmelden."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut."
        )
