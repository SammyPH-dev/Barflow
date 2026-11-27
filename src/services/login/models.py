"""
bruno

This module defines the base user type and role-specific user types used by
Barflow authentication. Passwords are hashed when a user is created and can
be verified without exposing the plaintext password.
"""

from pwdlib import PasswordHash


password_hasher = PasswordHash.recommended()


class User:
    """Represent a Barflow user with securely hashed credentials.

    Args:
        name: The user's first name.
        lastName: The user's last name.
        password: The plaintext password used to create the password hash.
        empNumber: The user's employee number.
        email: The user's email address.
        last_connected_at: The user's previous connection timestamp, or None.

    Raises:
        ValueError: If password is not a non-empty string.
    """

    def __init__(self,username, name, lastName, password, empNumber, email, last_connected_at):
        self.username = username
        self.name = name
        self.lastname = lastName
        if not isinstance(password, str) or not password:
            raise ValueError("Password must not be empty.")
        self.password_hash = password_hasher.hash(password)
        self.empNumber = empNumber
        self.email = email
        self.last_connected_at = last_connected_at

    def verify_password(self, password):
        """Verify a plaintext password against this user's stored hash.

        Args:
            password: The plaintext password to verify.

        Returns:
            True when the password matches; otherwise, False.
        """
        return password_hasher.verify(password, self.password_hash)

    def __str__(self):
        """Return a readable summary of the user."""
        return f"{self.name} {self.lastname} ({self.empNumber})"

class Manager(User):
    """Represent a Barflow user with the manager role."""

    def __init__(self,username, name, lastName, password, empNumber, email, last_connected_at):
        super().__init__(username,name, lastName, password, empNumber, email, last_connected_at)
        self.role = "Manager"


class Employee(User):
    """Represent a Barflow user with the employee role."""

    def __init__(self,username, name, lastName, password, empNumber, email, last_connected_at):
        super().__init__(username,name, lastName, password, empNumber, email, last_connected_at)
        self.role = "Employee"