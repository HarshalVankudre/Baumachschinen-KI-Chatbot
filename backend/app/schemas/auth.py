"""Authentication schemas for API requests and responses."""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegistration(BaseModel):
    """User registration request schema."""
    username: str = Field(min_length=3, max_length=30, description="Username (3-30 characters)")
    email: EmailStr = Field(description="Email address")
    password: str = Field(min_length=12, description="Password (minimum 12 characters)")
    confirm_password: str = Field(description="Password confirmation")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not v.isalnum() and "_" not in v and "-" not in v:
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters long")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)

        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, one number, and one special character"
            )
        return v


class UserLogin(BaseModel):
    """User login request schema."""
    username: str = Field(description="Username or email")
    password: str = Field(description="Password")
    remember_me: bool = Field(default=False, description="Remember me for extended session")


class UserResponse(BaseModel):
    """User data response schema."""
    user_id: str = Field(description="User ID")
    username: str = Field(description="Username")
    email: str = Field(description="Email address")
    authorization_level: Literal['regular', 'superuser', 'admin'] = Field(description="Authorization level")
    account_status: str = Field(description="Account status")
    email_verified: bool = Field(description="Email verification status")
    created_at: datetime = Field(description="Account creation timestamp")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")


class EmailVerificationRequest(BaseModel):
    """Email verification request schema."""
    token: str = Field(description="Email verification token")


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    current_password: str = Field(description="Current password")
    new_password: str = Field(min_length=12, description="New password")
    confirm_password: str = Field(description="Confirm new password")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters long")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)

        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, one number, and one special character"
            )
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: EmailStr = Field(description="Email address for password reset")


class PasswordResetTokenVerification(BaseModel):
    """Password reset token verification schema."""
    token: str = Field(description="Password reset token")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str = Field(description="Password reset token")
    new_password: str = Field(min_length=12, description="New password")
    confirm_password: str = Field(description="Confirm new password")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters long")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)

        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, one number, and one special character"
            )
        return v