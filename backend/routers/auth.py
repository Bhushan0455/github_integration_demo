"""
routers/auth.py — GitHub OAuth Authentication Routes
=====================================================
This file handles the entire "Sign in with GitHub" flow.

HOW GITHUB OAUTH WORKS (step by step):
=======================================

1. User clicks "Sign in with GitHub" on our frontend
2. Frontend redirects to our backend: GET /auth/github
3. Our backend redirects the user to GitHub's login page:
   https://github.com/login/oauth/authorize?client_id=xxx&redirect_uri=xxx
4. User logs in on GitHub and clicks "Authorize"
5. GitHub redirects the user BACK to our backend:
   GET /auth/callback?code=TEMPORARY_CODE
6. Our backend sends this "code" to GitHub to exchange it for an ACCESS TOKEN
   POST https://github.com/login/oauth/access_token
7. We use the access token to fetch the user's profile (username, avatar)
   GET https://api.github.com/user
8. We save the user in our database
9. We redirect the user back to the frontend dashboard with their info

IMPORTANT: The OAuth access token is ONLY used for login/profile.
           It is NOT used to access repositories. That's the GitHub App's job (Phase 3).
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx

from database import get_db
from models import User

# ── Create the router ──────────────────────────────────────────────
# A "router" is like a mini-app that groups related routes together.
# All routes in this file will start with "/auth"
router = APIRouter(prefix="/auth", tags=["Authentication"])

# ── Read OAuth credentials from environment variables ──────────────
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# ── GitHub OAuth URLs (these are fixed, defined by GitHub) ─────────
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API_URL = "https://api.github.com/user"


# ════════════════════════════════════════════════════════════════════
# ROUTE 1: Start the OAuth flow
# ════════════════════════════════════════════════════════════════════
@router.get("/github")
def github_login():
    """
    STEP 1: Redirect the user to GitHub's login/authorization page.

    When the user clicks "Sign in with GitHub" on our frontend, they
    hit this route. We redirect them to GitHub with our client_id.

    The "scope=read:user" tells GitHub we only want to read the user's
    profile (username, avatar). We do NOT ask for repo access here.

    Flow: Frontend → /auth/github → GitHub Login Page
    """

    # ── Build the GitHub authorization URL ──────────────────────
    # client_id:    Tells GitHub "this is my app"
    # redirect_uri: Where GitHub should send the user after they log in
    # scope:        What permissions we're asking for (just profile info)
    redirect_uri = f"http://localhost:8000/auth/callback"
    github_auth_url = (
        f"{GITHUB_AUTHORIZE_URL}"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=read:user"
    )

    # Send the user to GitHub
    return RedirectResponse(url=github_auth_url)


# ════════════════════════════════════════════════════════════════════
# ROUTE 2: Handle the OAuth callback from GitHub
# ════════════════════════════════════════════════════════════════════
@router.get("/callback")
async def github_callback(code: str, db: Session = Depends(get_db)):
    """
    STEP 2: GitHub redirects the user back here with a temporary "code".

    This is the most important route. Here's what happens:
    a) GitHub sends us a temporary "code" in the URL: /auth/callback?code=abc123
    b) We exchange this code for a permanent "access_token" by calling GitHub's API
    c) We use the access_token to fetch the user's profile (username, avatar)
    d) We save/update the user in our database
    e) We redirect the user to the frontend dashboard

    The "code" is like a one-time password:
    - It can only be used ONCE
    - It expires in 10 minutes
    - It must be exchanged for an access_token on the server side (not in the browser)

    Flow: GitHub → /auth/callback?code=xxx → Exchange for token → Fetch profile → Redirect to frontend
    """

    # ── Step A: Exchange the temporary code for an access_token ─────
    # We send the code + our client_id + client_secret to GitHub.
    # GitHub verifies everything and gives us back an access_token.
    # Think of it like: "Here's my ID (client_id), my password (client_secret),
    # and the one-time code the user gave me. Give me a real token."
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,  # The temporary code from GitHub
            },
            headers={
                # Tell GitHub to respond with JSON (not URL-encoded text)
                "Accept": "application/json",
            },
        )

    token_data = token_response.json()

    # Check if the exchange worked
    access_token = token_data.get("access_token")
    if not access_token:
        # Something went wrong — maybe the code expired or was already used
        raise HTTPException(
            status_code=400,
            detail=f"Failed to get access token from GitHub: {token_data}",
        )

    # ── Step B: Use the access_token to fetch the user's profile ────
    # Now that we have a valid token, we can call GitHub's API to get
    # the user's profile information (username, avatar, etc.)
    # The token goes in the "Authorization" header.
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            GITHUB_USER_API_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )

    github_user = user_response.json()

    # Extract the fields we care about
    github_id = github_user["id"]           # Unique numeric ID on GitHub
    username = github_user["login"]          # GitHub username (e.g., "bhushan")
    avatar_url = github_user["avatar_url"]   # Profile picture URL

    # ── Step C: Save or update the user in our database ─────────────
    # Check if this GitHub user already exists in our database
    existing_user = db.query(User).filter(User.github_id == github_id).first()

    if existing_user:
        # User already exists — update their info (in case they changed their avatar, etc.)
        existing_user.username = username
        existing_user.avatar_url = avatar_url
        existing_user.access_token = access_token  # ⚠️ Demo only — see security note
        db.commit()
        db.refresh(existing_user)
    else:
        # New user — create a new record in the database
        new_user = User(
            github_id=github_id,
            username=username,
            avatar_url=avatar_url,
            access_token=access_token,  # ⚠️ Demo only — see security note
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    # ── Step D: Redirect to the frontend dashboard ──────────────────
    # We send the access_token and user info as URL query parameters.
    #
    # ⚠️  SECURITY NOTE FOR PRODUCTION:
    # Passing tokens in URLs is NOT secure for production apps because:
    # - Tokens appear in browser history
    # - Tokens appear in server logs
    # - Tokens can leak via the Referer header
    # In production, use secure HTTP-only cookies instead.
    # We use URL params here because it's simpler to understand for learning.
    redirect_url = (
        f"{FRONTEND_URL}/dashboard"
        f"?token={access_token}"
        f"&username={username}"
        f"&avatar_url={avatar_url}"
    )

    return RedirectResponse(url=redirect_url)


# ════════════════════════════════════════════════════════════════════
# ROUTE 3: Get current user info
# ════════════════════════════════════════════════════════════════════
@router.get("/me")
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Returns the currently logged-in user's profile.

    The frontend sends the access_token in the Authorization header:
        Authorization: Bearer gho_xxxxxxxxxxxx

    We look up the user in our database by their token and return their info.

    This route is called when the dashboard loads to verify the user is still logged in.
    """

    # ── Extract the token from the Authorization header ─────────────
    # The header looks like: "Bearer gho_xxxxxxxxxxxx"
    # We split on space and take the second part (the actual token)
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]

    # ── Look up the user by their access token ──────────────────────
    user = db.query(User).filter(User.access_token == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token — user not found")

    # ── Return the user's profile ───────────────────────────────────
    return {
        "id": user.id,
        "github_id": user.github_id,
        "username": user.username,
        "avatar_url": user.avatar_url,
    }
