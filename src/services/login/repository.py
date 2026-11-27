"""
bruno

mockdb for Barflow login testing.

This module provides the mockdb used by the login service and seeds it
with sample managers and employees. It is intended for development and testing
rather than persistent production storage.
"""

from src.services.login.models import Employee, Manager


class MockDatabase:
    """Store and retrieve users in memory using email addresses as keys."""

    def __init__(self):
        self._users = {}
        self._next_id = 1  # like the AUTO_INCREMENT of a real table

    def add_user(self, user):
        email = user._email.casefold()
        if email in self._users:
            raise ValueError(f"A user with email {user._email} already exists.")
        user._id = self._next_id
        self._next_id += 1
        self._users[email] = user

    def get_by_email(self, email):
        return self._users.get(email.casefold())

    def get_by_id(self, user_id):
        for user in self._users.values():
            if user._id == user_id:
                return user
        return None

    def save(self, user):
        self._users[user._email.casefold()] = user

    def get_recent_users(self, limit):
        if limit < 0:
            raise ValueError("Limit must not be negative.")

        users_with_login = []
        for user in self._users.values():
            if user._last_connected_at is not None:
                users_with_login.append(user)

        return sorted(
            users_with_login,
            key=lambda user: user._last_connected_at,
            reverse=True,
        )[:limit]


def create_user(user_class, username, name, lastname, password, emp_number, email):
    """Build a Manager or an Employee with a hashed password."""
    user = user_class(
        _username=username,
        _name=name,
        _lastname=lastname,
        _emp_number=emp_number,
        _email=email,
    )
    user.set_password(password)
    return user


mock_database = MockDatabase()

mock_database.add_user(create_user(Manager, "Sam P.-H.", "Sammy", "Panthaleon-Hernandez", "1234", "MGR001", "sammy@barflow.com"))
mock_database.add_user(create_user(Employee, "Bruno M.", "Bruno", "Mcnicoll", "1234", "EMP001", "bruno@barflow.com"))
mock_database.add_user(create_user(Employee, "Zac B.-C.", "Zacchary", "Bedard-Chenier", "1234", "EMP002", "Zacchary@barflow.com"))
mock_database.add_user(create_user(Employee, "Jason B.", "Jason", "Bussiere", "1234", "EMP003", "jason@barflow.com"))