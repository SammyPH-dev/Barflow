"""
Inventory Database Connection Module

This module creates the connection to the inventory database (MariaDB on Alwaysdata)
and gives one SQLAlchemy session to each request.

The database URL comes from the DATABASE_URL environment variable.
Never print or log the URL: it contains the password.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import config
from .default_ingredients import default_ingredients_if_db_empty
from .models import Base

engine = None
SessionLocal = None


def get_session():
    # FastAPI dependency
    # Gives one session and closes it when the request is finished.
    global engine, SessionLocal

    if SessionLocal is None:
        # pool_pre_ping checks that the connection is still alive before using it
        engine = create_engine(os.environ[config.DATABASE_URL_VARIABLE], pool_pre_ping=True)
        SessionLocal = sessionmaker(engine, expire_on_commit=False)

        # Creates the database tables if they do not exist
        Base.metadata.create_all(engine)

        # if the ingredient table is empty it is filled with the default ingredients
        with SessionLocal() as setup_session:
            default_ingredients_if_db_empty(setup_session)
            setup_session.commit()

    with SessionLocal() as session:
        yield session
