"""Audit log model for MongoDB."""
from datetime import datetime, UTC
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AuditLogModel(BaseModel):
    """Audit log document model for MongoDB."""
    log_id: str = Field(description="Unique log ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Action timestamp")
    admin_user_id: Optional[str] = Field(default=None, description="Admin user ID who performed action")
    admin_username: Optional[str] = Field(default=None, description="Admin username")
    action_type: str = Field(description="Action type")
    target_user_id: Optional[str] = Field(default=None, description="Target user ID (if applicable)")
    target_username: Optional[str] = Field(default=None, description="Target username (if applicable)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Action details")
    ip_address: Optional[str] = Field(default=None, description="Admin IP address")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "log_id": "log-550e8400",
                "timestamp": "2025-01-01T00:00:00Z",
                "admin_user_id": "admin-123",
                "admin_username": "admin",
                "action_type": "approve_user",
                "target_user_id": "user-456",
                "target_username": "johndoe",
                "details": {"authorization_level": "regular"},
                "ip_address": "192.168.1.1",
            }
        }
    )
