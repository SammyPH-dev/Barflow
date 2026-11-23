"""
bruno

FastAPI routes and authentication dependencies for the login service."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from .repository import mock_database
from .schemas import (
    CurrentUserResponse,
    LoginRequest,
    LoginResponse,
    RecentUsersResponse,
)
from .security import create_access_token, decode_access_token
from .service import InvalidCredentials, get_recent_users, login


router = APIRouter(prefix="/login", tags=["login"])
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """Resolve and validate the current user from a bearer access token.

    Args:
        credentials: Bearer credentials extracted from the request.

    Returns:
        The authenticated user instance.

    Raises:
        HTTPException: 401 if credentials are missing or the token/user is invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    email = payload.get("sub")
    user = mock_database.get_by_email(email) if isinstance(email, str) else None
    if user is None or payload.get("role") != user.role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("", response_model=LoginResponse)
def login_route(request: LoginRequest):
    """Authenticate credentials and return an access token.

    Args:
        request: Email and password credentials supplied by the client.

    Returns:
        A LoginResponse containing user details and an access token.

    Raises:
        HTTPException: 401 if the credentials are invalid.
    """
    try:
        user = login(request.email, request.password)
    except InvalidCredentials as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect.",
        ) from error

    return LoginResponse(
        authenticated=True,
        email=user.email,
        name=f"{user.name} {user.lastname}",
        role=user.role,
        access_token=create_access_token(user),
    )


@router.get("/recent-users", response_model=RecentUsersResponse)
def recent_users_route():
    """Return the users with the most recent successful logins.

    Returns:
        A RecentUsersResponse containing up to four recent users.
    """
    return get_recent_users()


@router.get("/me", response_model=CurrentUserResponse)
def current_user_route(user=Depends(get_current_user)):
    """Return public profile information for the current authenticated user.

    Args:
        user: The authenticated user resolved by get_current_user.

    Returns:
        A CurrentUserResponse containing email, name, and role.
    """
    return CurrentUserResponse(
        email=user.email,
        name=f"{user.name} {user.lastname}",
        role=user.role,
    )