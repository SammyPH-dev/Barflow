"""
Gateway Authentication Module

This module checks the token sent with a request and finds which user made it.
The services never check the token themselves: they trust the X-User-Id and X-User-Role
headers that the gateway adds after this check.

Author: Zacchary Bedard-Chenier
Date: 26/11/2026
Version: 1.0
"""

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from . import config

# Roles sent to the services, always in lowercase.
ROLES = ('employee', 'manager')


class AuthError(Exception):
    """Raised when a request has no valid token. Its message is sent back to the client."""


def read_user(authorization):
    """Checks the token of a request and returns the user it belongs to.

    # REMINDER FOR THE TEAM: the token is checked with the JWT secret from the gateway's local_settings.py,
    # which must have the same value as the login service's local_settings.py.

    Args:
        authorization (str | None): The Authorization header, ex: "Bearer <token>".

    Returns:
        tuple[str, str]: The user id (digits only) and the role in lowercase
        ("employee" or "manager").

    Raises:
        AuthError: If the token is missing, badly signed, expired, or does not contain
        a numeric user id ("sub") and a known role ("role").
    """
    if not authorization:
        raise AuthError('Bearer token required.')

    # Splits the authorization to only keep the token itself
    parts = authorization.split()  # ex: "Bearer eyJ..." -> ["Bearer", "eyJ..."]
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise AuthError('Bearer token required.')
    token = parts[1]

    # Checks the token: signature, expiry, and that "exp" and "sub" exist
    try:
        payload = jwt.decode(
            token,
            config.get_jwt_secret(),
            algorithms=[config.JWT_ALGORITHM],
            options={'require': ['exp', 'sub']},
        )
    except ExpiredSignatureError:
        raise AuthError('Expired token.')
    except InvalidTokenError:
        raise AuthError('Invalid token.')

    # The user id ("sub") must be a string of digits (ex: "7"),
    # because the services read X-User-Id as a whole number
    user_id = payload['sub']
    if not isinstance(user_id, str):
        raise AuthError('Invalid token.')
    if not user_id.isascii():  # isdigit() also accepts digits from other alphabets
        raise AuthError('Invalid token.')
    if not user_id.isdigit():
        raise AuthError('Invalid token.')

    # The role must be "employee" or "manager"
    # The login service may send "Manager" or "MANAGER",
    # it is put in lowercase so the services always get lowercase.
    role = payload.get('role')
    if not isinstance(role, str):
        raise AuthError('Invalid token.')
    role = role.lower()
    if role not in ROLES:
        raise AuthError('Invalid token.')

    return user_id, role
