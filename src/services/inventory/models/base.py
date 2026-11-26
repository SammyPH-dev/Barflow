"""
Inventory Base Model Module

This module defines the SQLAlchemy base class shared by every model of the inventory service.
Inspired by Jason's base classes from previous project ;)

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
