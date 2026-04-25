"""
models.py — Database Models (Tables)
=====================================
Each class here represents a TABLE in our SQLite database.
SQLAlchemy maps these Python classes to actual database tables.

We have 4 tables:
1. User          — stores GitHub users who log in via OAuth
2. Installation  — stores GitHub App installations (when a user installs our app)
3. Repository    — stores the repositories selected during installation
4. WebhookEvent  — stores incoming webhook events (like push notifications from GitHub)
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """
    Stores users who have logged in via GitHub OAuth.

    Example row:
    ┌────┬───────────┬──────────┬─────────────────────────────┬──────────────┐
    │ id │ github_id │ username │ avatar_url                  │ access_token │
    ├────┼───────────┼──────────┼─────────────────────────────┼──────────────┤
    │  1 │  12345678 │ bhushan  │ https://avatars.github...   │ gho_xxxx...  │
    └────┴───────────┴──────────┴─────────────────────────────┴──────────────┘

    NOTE on access_token:
    ⚠️  We store the OAuth access_token here for DEMO simplicity only.
        In a production app, you should NEVER store tokens in the database directly.
        Instead, use secure HTTP-only cookies or encrypted token storage.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # The user's unique ID on GitHub (stays the same even if they change username)
    github_id = Column(Integer, unique=True, nullable=False)

    # The user's GitHub username (e.g., "bhushan")
    username = Column(String, nullable=False)

    # URL to the user's GitHub profile picture
    avatar_url = Column(String, nullable=True)

    # ⚠️ OAuth access token — stored for demo only (see note above)
    access_token = Column(String, nullable=False)

    # When this user first logged in
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship: one user can have many installations
    installations = relationship("Installation", back_populates="user")


class Installation(Base):
    """
    Stores GitHub App installations.

    When a user installs our GitHub App on their account/org and selects
    repositories, GitHub gives us an "installation_id". We save it here.

    Example row:
    ┌────┬─────────────────┬─────────┬──────────────────────┐
    │ id │ installation_id │ user_id │ app_slug             │
    ├────┼─────────────────┼─────────┼──────────────────────┤
    │  1 │ 98765432        │ 1       │ my-github-demo-app   │
    └────┴─────────────────┴─────────┴──────────────────────┘
    """

    __tablename__ = "installations"

    id = Column(Integer, primary_key=True, index=True)

    # The unique installation ID that GitHub assigns when the app is installed
    # This is the key we use to get an "installation access token" via JWT
    installation_id = Column(Integer, unique=True, nullable=False)

    # Which user performed this installation (foreign key to users table)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # The slug (URL-friendly name) of our GitHub App
    app_slug = Column(String, nullable=True)

    # When this installation happened
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="installations")
    repositories = relationship("Repository", back_populates="installation")


class Repository(Base):
    """
    Stores repositories that were selected during GitHub App installation.

    When a user installs our GitHub App and picks "Only select repositories",
    those selected repos are saved here.

    Example row:
    ┌────┬─────────────────┬──────────────────────────┬────────────────┐
    │ id │ installation_id │ full_name                │ github_repo_id │
    ├────┼─────────────────┼──────────────────────────┼────────────────┤
    │  1 │ 1               │ bhushan/my-cool-project  │ 123456789      │
    └────┴─────────────────┴──────────────────────────┴────────────────┘
    """

    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key linking to the Installation that includes this repo
    installation_id = Column(
        Integer, ForeignKey("installations.id"), nullable=False
    )

    # Full name of the repo (e.g., "owner/repo-name")
    full_name = Column(String, nullable=False)

    # The repository's unique ID on GitHub
    github_repo_id = Column(Integer, nullable=True)

    # When this repo was added
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship back to installation
    installation = relationship("Installation", back_populates="repositories")


class WebhookEvent(Base):
    """
    Stores incoming webhook events from GitHub.

    Every time someone pushes code to a repo where our GitHub App is installed,
    GitHub sends us a "push" webhook. We log it here.

    Example row:
    ┌────┬────────────┬──────────────────┬──────────────┬───────────────────┬─────────────┐
    │ id │ event_type │ repo_name        │ commit_sha   │ changed_files     │ should_scan │
    ├────┼────────────┼──────────────────┼──────────────┼───────────────────┼─────────────┤
    │  1 │ push       │ bhushan/my-repo  │ abc123...    │ ["package.json"]  │ true        │
    └────┴────────────┴──────────────────┴──────────────┴───────────────────┴─────────────┘
    """

    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)

    # The type of event (e.g., "push", "pull_request", "installation")
    event_type = Column(String, nullable=False)

    # The full name of the repository (e.g., "owner/repo-name")
    repo_name = Column(String, nullable=True)

    # The SHA hash of the latest commit (a unique fingerprint for the commit)
    commit_sha = Column(String, nullable=True)

    # JSON string containing the list of files that were changed
    # Example: '["src/app.py", "README.md", "package.json"]'
    changed_files = Column(Text, nullable=True)

    # 🔍 Dependency detection flag:
    # Set to True if any changed file is a known dependency file
    # (package.json, package-lock.json, yarn.lock, pnpm-lock.yaml)
    # This flag will be used later for CVE scanning
    should_scan = Column(Boolean, default=False, nullable=False)

    # When we received this webhook
    received_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
