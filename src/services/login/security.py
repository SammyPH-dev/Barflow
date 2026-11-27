"""
bruno

JWT access-token creation and validation for the login service."""

from datetime import datetime, timedelta, timezone
import os
from importlib import import_module

import jwt
from jwt import InvalidTokenError

try:
    _local_jwt_secret = import_module(
        '.local_settings', package=__package__
    ).JWT_SECRET_KEY
except (ImportError, AttributeError):
    _local_jwt_secret = ''


def _get_secret_key():
    """Validate and return the JWT signing secret.

    Returns:
        The configured JWT secret key.

    Raises:
        RuntimeError: If the secret is missing or shorter than 32 characters.
    """
    secret_key = os.getenv('JWT_SECRET_KEY') or _local_jwt_secret
    if not secret_key or len(secret_key) < 32:
        raise RuntimeError("JWT_SECRET_KEY must contain at least 32 characters.")
    return secret_key


def create_access_token(user):
    """Create an HS256 access token for a user.

    Args:
        user: The authenticated user, containing email and role attributes.

    Returns:
        An encoded JWT string that expires after 30 minutes.
    """
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload = {
        "sub": user.email,
        "user_id": str(user.user_id),
        "role": user.role,
        "exp": expires_at,
    }
    return jwt.encode(payload, _get_secret_key(), algorithm="HS256")


def decode_access_token(token):
    """Decode and validate an HS256 JWT access token.

    Args:
        token: The encoded JWT string.

    Returns:
        The validated token payload.

    Raises:
        InvalidTokenError: If the token is invalid or expired.
    """
    return jwt.decode(token, _get_secret_key(), algorithms=["HS256"])
