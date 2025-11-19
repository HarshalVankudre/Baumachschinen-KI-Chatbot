"""
Admin Endpoints

Handles administrative functions:
- List pending users (GET /api/admin/users/pending)
- Approve user (POST /api/admin/users/{id}/approve)
- Reject user (POST /api/admin/users/{id}/reject)
- List all users (GET /api/admin/users)
- Change user authorization (PUT /api/admin/users/{id}/authorization)
- Get audit logs (GET /api/admin/audit-logs)
"""

import logging
import uuid
from datetime import datetime, UTC
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from app.core.database import get_database
from app.models.user import UserModel
from app.models.audit_log import AuditLogModel
from app.schemas.admin import (
    UserApproval,
    UserRejection,
    AuthorizationChange,
    AuditLogResponse,
)
from app.schemas.auth import UserResponse
from app.services.email_service import get_email_service
from app.api.v1.dependencies import require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


class PendingUsersResponse(BaseModel):
    """Response for pending users list"""
    pending_users: List[UserResponse]
    total: int


class UsersListResponse(BaseModel):
    """Response for all users list"""
    users: List[UserResponse]
    total: int
    limit: int
    offset: int


class AuditLogsResponse(BaseModel):
    """Response for audit logs list"""
    logs: List[AuditLogResponse]
    total: int
    limit: int
    offset: int


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


@router.get("/users/pending", response_model=PendingUsersResponse)
async def get_pending_users(
    admin: UserModel = Depends(require_admin)
) -> PendingUsersResponse:
    """
    Get list of users pending approval

    Returns users who have:
    - Verified their email (email_verified=true)
    - Account status 'pending_approval'

    Ordered by registration date (oldest first).
    """
    try:
        db = get_database()

        # Query pending users
        pending_users_cursor = db.users.find({
            "account_status": "pending_approval",
            "email_verified": True
        }).sort("created_at", 1)  # Oldest first

        pending_users = []
        async for user_doc in pending_users_cursor:
            user = UserModel(**user_doc)
            pending_users.append(
                UserResponse(
                    user_id=user.user_id,
                    username=user.username,
                    email=user.email,
                    authorization_level=user.authorization_level,
                    account_status=user.account_status,
                    email_verified=user.email_verified,
                    created_at=user.created_at,
                    last_login=user.last_login
                )
            )

        logger.info(f"Admin {admin.username} retrieved {len(pending_users)} pending users")

        return PendingUsersResponse(
            pending_users=pending_users,
            total=len(pending_users)
        )

    except Exception as e:
        logger.error(f"Error getting pending users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending users"
        )


@router.post("/users/{user_id}/approve", response_model=MessageResponse)
async def approve_user(
    user_id: str,
    approval_data: UserApproval,
    admin: UserModel = Depends(require_admin)
) -> MessageResponse:
    """
    Approve a pending user

    Process:
    1. Verify user exists and is pending approval
    2. Set account_status to 'active'
    3. Set authorization_level from request
    4. Record approval metadata (approved_by, approved_at)
    5. Send approval email to user
    6. Create audit log entry
    """
    try:
        db = get_database()

        # Find user
        user_doc = await db.users.find_one({"user_id": user_id})

        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user = UserModel(**user_doc)

        # Verify user is pending approval
        if user.account_status != "pending_approval":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User is not pending approval. Current status: {user.account_status}"
            )

        # Update user
        await db.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "account_status": "active",
                    "authorization_level": approval_data.authorization_level,
                    "approved_by": admin.user_id,
                    "approved_at": datetime.now(UTC)
                }
            }
        )

        logger.info(f"Admin {admin.username} approved user {user.username} with level {approval_data.authorization_level}")

        # Send approval email
        email_service = get_email_service()
        email_sent = await email_service.send_approval_email(
            email=user.email,
            username=user.username,
            authorization_level=approval_data.authorization_level
        )

        if not email_sent:
            logger.warning(f"Failed to send approval email to {user.email} for user {user.username}")
        else:
            logger.info(f"Approval email sent successfully to {user.email}")

        # Create audit log
        audit_log = AuditLogModel(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            action_type="approve_user",
            admin_user_id=admin.user_id,
            admin_username=admin.username,
            target_user_id=user.user_id,
            target_username=user.username,
            details={
                "authorization_level": approval_data.authorization_level,
                "previous_status": "pending_approval",
                "new_status": "active"
            }
        )
        await db.audit_logs.insert_one(audit_log.model_dump())

        return MessageResponse(
            message=f"User {user.username} approved successfully with {approval_data.authorization_level} access"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve user"
        )


@router.post("/users/{user_id}/reject", response_model=MessageResponse)
async def reject_user(
    user_id: str,
    rejection_data: UserRejection,
    admin: UserModel = Depends(require_admin)
) -> MessageResponse:
    """
    Reject a user registration

    Process:
    1. Verify user exists
    2. Set account_status to 'rejected'
    3. Record rejection metadata (rejected_by, rejected_at, reason)
    4. Send rejection email with optional reason
    5. Create audit log entry
    """
    try:
        db = get_database()

        # Find user
        user_doc = await db.users.find_one({"user_id": user_id})

        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user = UserModel(**user_doc)

        # Update user
        await db.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "account_status": "rejected",
                    "rejected_by": admin.user_id,
                    "rejected_at": datetime.now(UTC),
                    "rejection_reason": rejection_data.reason
                }
            }
        )

        logger.info(f"Admin {admin.username} rejected user {user.username}")

        # Send rejection email
        email_service = get_email_service()
        email_sent = await email_service.send_rejection_email(
            email=user.email,
            username=user.username,
            reason=rejection_data.reason
        )

        if not email_sent:
            logger.warning(f"Failed to send rejection email to {user.email} for user {user.username}")
        else:
            logger.info(f"Rejection email sent successfully to {user.email}")

        # Create audit log
        audit_log = AuditLogModel(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            action_type="reject_user",
            admin_user_id=admin.user_id,
            admin_username=admin.username,
            target_user_id=user.user_id,
            target_username=user.username,
            details={
                "reason": rejection_data.reason,
                "previous_status": user.account_status,
                "new_status": "rejected"
            }
        )
        await db.audit_logs.insert_one(audit_log.model_dump())

        return MessageResponse(
            message=f"User {user.username} rejected successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject user"
        )


@router.get("/users", response_model=UsersListResponse)
async def list_all_users(
    admin: UserModel = Depends(require_admin),
    status_filter: Optional[str] = Query(default=None, description="Filter by account status"),
    authorization_level: Optional[str] = Query(default=None, description="Filter by authorization level"),
    search: Optional[str] = Query(default=None, description="Search by username or email"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0)
) -> UsersListResponse:
    """
    List all users with filtering

    Supports filtering by:
    - Account status (active, pending_approval, rejected, suspended)
    - Authorization level (regular, superuser, admin)
    - Search (username or email)

    Includes pagination.
    """
    try:
        db = get_database()

        # Build query filter
        filter_query = {}

        if status_filter:
            filter_query["account_status"] = status_filter

        if authorization_level:
            filter_query["authorization_level"] = authorization_level

        if search:
            filter_query["$or"] = [
                {"username": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]

        # Get total count
        total = await db.users.count_documents(filter_query)

        # Get users with pagination
        users_cursor = db.users.find(filter_query)\
            .sort("created_at", -1)\
            .skip(offset)\
            .limit(limit)

        users_list = []
        async for user_doc in users_cursor:
            user = UserModel(**user_doc)
            users_list.append(
                UserResponse(
                    user_id=user.user_id,
                    username=user.username,
                    email=user.email,
                    authorization_level=user.authorization_level,
                    account_status=user.account_status,
                    email_verified=user.email_verified,
                    created_at=user.created_at,
                    last_login=user.last_login
                )
            )

        logger.info(f"Admin {admin.username} listed {len(users_list)} users")

        return UsersListResponse(
            users=users_list,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.put("/users/{user_id}/authorization", response_model=MessageResponse)
async def change_user_authorization(
    user_id: str,
    authorization_data: AuthorizationChange,
    admin: UserModel = Depends(require_admin)
) -> MessageResponse:
    """
    Change user authorization level

    Allows changing between: regular, superuser, admin

    Restrictions:
    - Admin cannot change their own authorization level
    - Change takes effect on user's next login
    """
    try:
        db = get_database()

        # Prevent admin from changing their own level
        if user_id == admin.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own authorization level"
            )

        # Find user
        user_doc = await db.users.find_one({"user_id": user_id})

        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user = UserModel(**user_doc)
        previous_level = user.authorization_level

        # Update authorization level
        await db.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "authorization_level": authorization_data.authorization_level
                }
            }
        )

        logger.info(f"Admin {admin.username} changed {user.username} authorization from {previous_level} to {authorization_data.authorization_level}")

        # Send role change notification email to user
        email_service = get_email_service()
        email_sent = await email_service.send_role_change_email(
            email=user.email,
            username=user.username,
            old_level=previous_level,
            new_level=authorization_data.authorization_level
        )

        if not email_sent:
            logger.warning(f"Failed to send role change email to {user.email}")
        else:
            logger.info(f"Role change email sent successfully to {user.email}")

        # Create audit log
        audit_log = AuditLogModel(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            action_type="change_authorization",
            admin_user_id=admin.user_id,
            admin_username=admin.username,
            target_user_id=user.user_id,
            target_username=user.username,
            details={
                "previous_level": previous_level,
                "new_level": authorization_data.authorization_level
            }
        )
        await db.audit_logs.insert_one(audit_log.model_dump())

        return MessageResponse(
            message=f"Authorization level for {user.username} changed from {previous_level} to {authorization_data.authorization_level}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing authorization: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change authorization level"
        )


@router.get("/audit-logs", response_model=AuditLogsResponse)
async def get_audit_logs(
    admin: UserModel = Depends(require_admin),
    start_date: Optional[datetime] = Query(default=None, description="Filter logs after this date"),
    end_date: Optional[datetime] = Query(default=None, description="Filter logs before this date"),
    action_type: Optional[str] = Query(default=None, description="Filter by action type"),
    admin_user_id: Optional[str] = Query(default=None, description="Filter by admin who performed action"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0)
) -> AuditLogsResponse:
    """
    Get audit logs

    Returns immutable audit trail of admin actions.

    Supports filtering by:
    - Date range (start_date, end_date)
    - Action type (approve_user, reject_user, change_authorization, etc.)
    - Admin who performed action

    Ordered by timestamp (most recent first).
    """
    try:
        db = get_database()

        # Build query filter
        filter_query = {}

        if start_date or end_date:
            filter_query["timestamp"] = {}
            if start_date:
                filter_query["timestamp"]["$gte"] = start_date
            if end_date:
                filter_query["timestamp"]["$lte"] = end_date

        if action_type:
            filter_query["action_type"] = action_type

        if admin_user_id:
            filter_query["admin_user_id"] = admin_user_id

        # Get total count
        total = await db.audit_logs.count_documents(filter_query)

        # Get logs with pagination
        logs_cursor = db.audit_logs.find(filter_query)\
            .sort("timestamp", -1)\
            .skip(offset)\
            .limit(limit)

        logs_list = []
        async for log_doc in logs_cursor:
            log = AuditLogModel(**log_doc)
            logs_list.append(
                AuditLogResponse(
                    log_id=log.log_id,
                    timestamp=log.timestamp,
                    action_type=log.action_type,
                    admin_username=log.admin_username or "system",
                    target_username=log.target_username,
                    details=log.details
                )
            )

        logger.info(f"Admin {admin.username} retrieved {len(logs_list)} audit logs")

        return AuditLogsResponse(
            logs=logs_list,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error retrieving audit logs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )
