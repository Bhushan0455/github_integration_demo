"""
database.py — Database Connection Setup
========================================
This file sets up the connection to our SQLite database using SQLAlchemy.

Think of it like this:
- "engine"       = the connection to the database file
- "SessionLocal" = a factory that creates database sessions (like opening a tab in a browser)
- "Base"         = the parent class that all our database models will inherit from

We use SQLite here because it's a single file — no need to install PostgreSQL or MySQL.
The database file (github_demo.db) is created automatically when the app starts.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load variables from the .env file into the environment
load_dotenv()

# Read the database URL from .env (defaults to a local SQLite file)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./github_demo.db")

# ── Create the database engine ──────────────────────────────────────
# The engine is the starting point for any SQLAlchemy application.
# connect_args={"check_same_thread": False} is needed for SQLite only,
# because SQLite by default only allows access from the thread that created it.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite-specific setting
    echo=False,  # Set to True to see all SQL queries in the terminal (useful for debugging)
)

# ── Create a session factory ────────────────────────────────────────
# A "session" is like a conversation with the database.
# - autocommit=False: we manually decide when to save changes
# - autoflush=False:  we manually decide when to send changes to the DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Create the base class for models ────────────────────────────────
# All our database models (User, Installation, etc.) will inherit from this.
# It gives them the ability to map Python classes to database tables.
Base = declarative_base()


def get_db():
    """
    Dependency function for FastAPI routes.

    Usage in a route:
        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...

    This creates a new database session for each request,
    and automatically closes it when the request is done.
    Think of it like: open a connection → do your work → close the connection.
    """
    db = SessionLocal()
    try:
        yield db  # Give the session to the route function
    finally:
        db.close()  # Always close the session when done
