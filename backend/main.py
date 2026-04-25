"""
main.py — FastAPI Application Entry Point
==========================================
This is the "starting file" for our backend server.
Think of it like the "index.js" or "app.js" in a Node/Express project.

What it does:
1. Creates the FastAPI app
2. Adds CORS middleware (so our React frontend can talk to this backend)
3. Creates all database tables on startup
4. Will include routers for auth, installations, and webhooks (in later phases)

To run this server:
    cd backend
    uvicorn main:app --reload --port 8000
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file FIRST, before anything else
load_dotenv()

# Import our database setup
from database import engine, Base

# ── Create the FastAPI application ──────────────────────────────────
app = FastAPI(
    title="GitHub Integration Demo",
    description="A demo project to learn GitHub OAuth, GitHub Apps, and Webhooks",
    version="1.0.0",
)

# ── CORS Middleware ─────────────────────────────────────────────────
# CORS = Cross-Origin Resource Sharing
#
# Problem: Our frontend (localhost:5173) and backend (localhost:8000) are on
# different "origins" (different ports = different origins).
# By default, browsers BLOCK requests between different origins for security.
#
# Solution: We tell our backend "it's okay to accept requests from our frontend".
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],    # Only allow our frontend
    allow_credentials=True,           # Allow cookies/auth headers
    allow_methods=["*"],              # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],              # Allow all headers
)


# ── Startup Event: Create Database Tables ───────────────────────────
@app.on_event("startup")
def on_startup():
    """
    This function runs ONCE when the server starts.
    It creates all database tables defined in models.py.
    If the tables already exist, it does nothing (safe to run multiple times).
    """
    # Import models so SQLAlchemy knows about them
    import models  # noqa: F401 — we import for side effects (table registration)

    # Create all tables in the database
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created successfully!")


# ── Health Check Route ──────────────────────────────────────────────
@app.get("/")
def health_check():
    """
    A simple route to verify the server is running.
    Visit http://localhost:8000/ in your browser to test.
    """
    return {
        "status": "running",
        "message": "GitHub Integration Demo API is live! 🚀",
    }


# ── Router Includes ────────────────────────────────────────────────
# Phase 2: OAuth authentication routes (/auth/*)
from routers.auth import router as auth_router
app.include_router(auth_router)

# Phase 3: app.include_router(installations_router)
# Phase 4: app.include_router(webhooks_router)
