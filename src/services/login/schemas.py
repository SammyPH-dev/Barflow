"""
bruno

Pydantic request and response schemas for the login API."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Credentials submitted to the login endpoint."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class RecentUser(BaseModel):
    """Public summary of a user with a recent successful login."""

    email: EmailStr
    name: str
    last_connected_at: datetime


class RecentUsersResponse(BaseModel):
    """Response containing users ordered by recent login activity."""

    recent_users: list[RecentUser]


class LoginResponse(BaseModel):
    """Authentication result, authenticated user data, and access token."""

    authenticated: bool
    id: int
    email: str
    name: str
    role: str
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    """Public profile information for the authenticated user."""

    id: int
    email: EmailStr
    name: str
    role: str