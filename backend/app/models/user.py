"""User model for MongoDB."""
from datetime import datetime, UTC
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserModel(BaseModel):
    """User document model for MongoDB."""
    user_id: str = Field(description="Unique user ID")
    username: str = Field(description="Username (unique, lowercase)")
    email: EmailStr = Field(description="Email address (unique)")
    password_hash: str = Field(description="Argon2 hashed password")
    authorization_level: str = Field(default="regular", description="Authorization level: regular, superuser, admin")
    account_status: str = Field(default="pending_verification", description="Account status")
    email_verified: bool = Field(default=False, description="Email verification status")
    email_verification_token: Optional[str] = Field(default=None, description="Email verification token")
    email_verification_expires: Optional[datetime] = Field(default=None, description="Token expiration")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Account creation timestamp")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")
    approved_by: Optional[str] = Field(default=None, description="Admin user_id who approved")
    approved_at: Optional[datetime] = Field(default=None, description="Approval timestamp")
    rejected_by: Optional[str] = Field(default=None, description="Admin user_id who rejected")
    rejected_at: Optional[datetime] = Field(default=None, description="Rejection timestamp")
    settings: Dict[str, Any] = Field(default_factory=dict, description="User settings and preferences")
    # Password reset fields
    password_reset_token: Optional[str] = Field(default=None, description="Password reset token")
    password_reset_expires: Optional[datetime] = Field(default=None, description="Password reset token expiration")
    password_reset_attempts: int = Field(default=0, description="Number of password reset attempts in current window")
    password_reset_last_attempt: Optional[datetime] = Field(default=None, description="Last password reset attempt timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "johndoe",
                "email": "john@example.com",
                "password_hash": "$argon2id$...",
                "authorization_level": "regular",
                "account_status": "active",
                "email_verified": True,
                "created_at": "2025-01-01T00:00:00Z",
            }
        }
    )


class SessionModel(BaseModel):
    """Session document model for MongoDB."""
    session_id: str = Field(description="Unique session ID (token)")
    user_id: str = Field(description="User ID")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Session creation timestamp")
    expires_at: datetime = Field(description="Session expiration timestamp")
    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    user_agent: Optional[str] = Field(default=None, description="Client user agent")
