"""
bruno

This module defines the user database model and its role-specific subclasses
used by Barflow authentication. Manager and Employee are saved in the same
"user" table: the _role column says which one a row is. Only the password hash
is stored, set with set_password() and checked with verify_password().
"""
import enum

from pwdlib import PasswordHash
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import DeclarativeBase

password_hasher = PasswordHash.recommended()

class Role(str, enum.Enum):
    MANAGER = "manager"
    EMPLOYEE = "employee"

class Base(DeclarativeBase):
    pass

class User(Base):
    """Represent a Barflow user (base class of Manager and Employee).

    Columns:
        _id: Number given by the database, sent in the token ("sub").
        _username: Short name shown in the application.
        _name: First name.
        _lastname: Last name.
        _emp_number: Employee number (ex: "MGR001"), unique.
        _email: Email address used to log in, unique.
        _password_hash: Hash of the password, never the password itself.
        _role: "manager" or "employee", set by the subclass.
        _last_connected_at: Date of the last successful login (UTC), or None.
    """
    __tablename__ = "user"
    _id = Column(Integer, primary_key=True, autoincrement=True)
    _username = Column(String(50), nullable=False)
    _name = Column(String(100), nullable=False)
    _lastname = Column(String(100), nullable=False)
    _emp_number = Column(String(20), nullable=False, unique=True)
    _email = Column(String(255), nullable=False, unique=True)
    _password_hash = Column(String(255), nullable=False)
    _role = Column(Enum(Role), nullable=False)
    _last_connected_at = Column(DateTime(timezone=True), nullable=True)

    # Manager and Employee are saved in this same table, _role says which one a row is
    __mapper_args__ = {'polymorphic_on': _role}

    def set_password(self, password):
        """Hash a plaintext password and store the hash.

        Raises:
            ValueError: If password is not a non-empty string.
        """
        if not isinstance(password, str) or not password:
            raise ValueError('Password must not be empty.')
        self._password_hash = password_hasher.hash(password)

    def verify_password(self, password):
        """Return True when the plaintext password matches the stored hash."""
        return password_hasher.verify(password, self._password_hash)

    def __str__(self):
        return f'{self._name} {self._lastname} ({self._emp_number})'


class Manager(User):
    """Represent a Barflow user with the manager role."""

    __mapper_args__ = {'polymorphic_identity': Role.MANAGER}


class Employee(User):
    """Represent a Barflow user with the employee role."""

    __mapper_args__ = {'polymorphic_identity': Role.EMPLOYEE}
