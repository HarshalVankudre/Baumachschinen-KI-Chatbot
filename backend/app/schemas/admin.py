"""Admin schemas for API requests and responses."""
from datetime import datetime
from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field


class UserApproval(BaseModel):
    """User approval request schema."""
    authorization_level: Literal['regular', 'superuser', 'admin'] = Field(description="Authorization level to assign")


class UserRejection(BaseModel):
    """User rejection request schema."""
    reason: Optional[str] = Field(default=None, max_length=500, description="Rejection reason (optional)")


class AuthorizationChange(BaseModel):
    """Authorization level change request schema."""
    authorization_level: Literal['regular', 'superuser', 'admin'] = Field(description="New authorization level")


class AuditLogResponse(BaseModel):
    """Audit log response schema."""
    log_id: str = Field(description="Audit log ID")
    timestamp: datetime = Field(description="Action timestamp")
    admin_user_id: Optional[str] = Field(default=None, description="Admin user ID")
    admin_username: Optional[str] = Field(default=None, description="Admin username")
    action_type: str = Field(description="Action type (e.g., approve_user, reject_user, change_authorization)")
    target_user_id: Optional[str] = Field(default=None, description="Target user ID (if applicable)")
    target_username: Optional[str] = Field(default=None, description="Target username (if applicable)")
    details: Dict[str, Any] = Field(description="Action details")
    ip_address: Optional[str] = Field(default=None, description="Admin IP address")


class AuditLogListResponse(BaseModel):
    """Audit log list response schema."""
    logs: List[AuditLogResponse] = Field(description="List of audit logs")
    total: int = Field(description="Total number of logs")
    limit: int = Field(description="Limit used in query")
    offset: int = Field(description="Offset used in query")


class PendingUserResponse(BaseModel):
    """Pending user response schema."""
    user_id: str = Field(description="User ID")
    username: str = Field(description="Username")
    email: str = Field(description="Email address")
    created_at: datetime = Field(description="Registration timestamp")
    email_verified: bool = Field(description="Email verification status")
    account_status: str = Field(description="Account status")


class UserManagementResponse(BaseModel):
    """User management list response schema."""
    users: List[Dict[str, Any]] = Field(description="List of users with full details")
    total: int = Field(description="Total number of users")
    limit: int = Field(description="Limit used in query")
    offset: int = Field(description="Offset used in query")


class AdminActionResponse(BaseModel):
    """Generic admin action response schema."""
    success: bool = Field(description="Whether action was successful")
    message: str = Field(description="Status message")
    user_id: Optional[str] = Field(default=None, description="Affected user ID")
