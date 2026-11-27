"""
bruno

mockdb for Barflow login testing.

This module provides the mockdb used by the login service and seeds it
with sample managers and employees. It is intended for development and testing
rather than persistent production storage.
"""

from .models import Manager, Employee


class MockDatabase:
    """Store and retrieve users in memory using email addresses as keys."""

    def __init__(self):
        """Initialize an empty in-memory user collection."""
        self._users = {}
        self._next_user_id = 1

    def add_user(self, user):
        """Add a user to the database.

        Args:
            user: The user instance to add.

        Raises:
            ValueError: If another user already has the same email address.
        """
        email = user.email.casefold()
        if email in self._users:
            raise ValueError(f"A user with email {user.email} already exists.")
        user.user_id = self._next_user_id
        self._next_user_id += 1
        self._users[email] = user

    def get_by_email(self, email):
        """Look up a user by email address, casefold: makes all text lowercase for comparison.

        Args:
            email: The email address to find.

        Returns:
            The matching user, or None when no user exists.
        """
        return self._users.get(email.casefold())

    def save(self, user):
        """Insert or update a user in the in-memory database.

        Args:
            user: The user instance to save.
        """
        self._users[user.email.casefold()] = user

    def get_recent_users(self, limit):
        """Return the most recently connected users.

        Args:
            limit: Maximum number of users to return.

        Returns:
            A list ordered from the latest connection to the earliest.

        Raises:
            ValueError: If limit is negative.
        """
        if limit < 0:
            raise ValueError("Limit must not be negative.")

        users_with_login = []
        for user in self._users.values():
            if user.last_connected_at is not None:
                users_with_login.append(user)

        return sorted(
            users_with_login,
            key=lambda user: user.last_connected_at,
            reverse=True,
        )[:limit]


mock_database = MockDatabase()

sammy = Manager(
    "Sam P.-H.",
    "Sammy",
    "Panthaleon-Hernandez",
    "1234",
    "MGR001",
    "sammy@barflow.com",
    None
)
bruno = Employee(
    "Bruno M.",
    "Bruno",
    "Mcnicoll",
    "1234",
    "EMP001",
    "bruno@barflow.com",
    None
)
zacchary = Employee(
    "Zac B.-C.",
    "Zacchary",
    "Bedard-Chenier",
    "1234",
    "EMP002",
    "Zacchary@barflow.com",
    None
)
jason = Employee(
    "Jason B.",
    "Jason",
    "Bussiere",
    "1234",
    "EMP003",
    "jason@barflow.com",
    None
)
mock_database.add_user(sammy)
mock_database.add_user(bruno)
mock_database.add_user(zacchary)
mock_database.add_user(jason)
