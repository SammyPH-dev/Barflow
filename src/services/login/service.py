"""
bruno

Business logic for user authentication and recent-login queries."""

from datetime import datetime, timezone

from .repository import mock_database
from .schemas import RecentUser, RecentUsersResponse


class InvalidCredentials(Exception):
    """Raised when an email address or password is invalid."""


def login(email, password, database=mock_database):
    """Authenticate a user and record their successful login.

    Args:
        email: The email address supplied by the user.
        password: The plaintext password supplied by the user.
        database: The user repository used for lookup and persistence.

    Returns:
        The authenticated user instance.

    Raises:
        InvalidCredentials: If the email is unknown or the password is invalid.
    """
    user = database.get_by_email(email)
    if user is None or not user.verify_password(password):
        raise InvalidCredentials("Email or password is incorrect.")

    now = datetime.now(timezone.utc)
    user.last_connected_at = now
    database.save(user)
    return user


def get_recent_users(database=mock_database):
    """Build a response containing the four most recent logged-in users.

    Args:
        database: The user repository used to retrieve recent users.

    Returns:
        A RecentUsersResponse populated with recent-user summaries.
    """
    users = database.get_recent_users(limit=4)
    return RecentUsersResponse(
        recent_users=[
            RecentUser(
                email=user.email,
                name=f"{user.name} {user.lastname}",
                last_connected_at=user.last_connected_at,
            )
            for user in users
        ]
    )
