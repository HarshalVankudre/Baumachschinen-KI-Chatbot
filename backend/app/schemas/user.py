"""User settings and profile schemas."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class UserSettings(BaseModel):
    """User settings schema."""
    ui_language: str = Field(default="en", description="UI language code")
    theme: str = Field(default="light", description="UI theme preference")
    notifications_enabled: bool = Field(default=True, description="Email notifications enabled")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="Additional user preferences")


class UserSettingsUpdate(BaseModel):
    """User settings update request schema."""
    ui_language: Optional[str] = Field(default=None, description="UI language code")
    theme: Optional[str] = Field(default=None, description="UI theme preference")
    notifications_enabled: Optional[bool] = Field(default=None, description="Email notifications enabled")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="Additional user preferences")
