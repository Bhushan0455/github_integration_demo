"""
github_jwt.py — GitHub App Authentication
==========================================
Unlike OAuth user authentication, authenticating as a GitHub App
requires generating a JSON Web Token (JWT) signed with your App's private key.

Step 1: Create a JWT signed with your RS256 private key. This token proves
        you are the GitHub App. It is only valid for 10 minutes.
Step 2: Use the JWT to call GitHub's API to get an "installation access token".
        This token proves you have permission to access the specific repositories
        the user selected during installation. It is valid for 1 hour.
"""

import os
import time
import jwt
import httpx
from fastapi import HTTPException

# ── Step 1: Generate App JWT ─────────────────────────────────────────
def generate_app_jwt() -> str:
    """
    Generates a JWT to authenticate as the GitHub App.
    """
    app_id = os.getenv("GITHUB_APP_ID")
    if not app_id:
        raise HTTPException(status_code=500, detail="GITHUB_APP_ID missing in .env")

    # Read the private key. It can be provided as a file path or a string.
    private_key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH")
    private_key = os.getenv("GITHUB_PRIVATE_KEY")
    
    if private_key_path and os.path.exists(private_key_path):
        with open(private_key_path, 'r') as key_file:
            private_key = key_file.read()
    elif not private_key:
        raise HTTPException(
            status_code=500, 
            detail="GITHUB_PRIVATE_KEY or GITHUB_PRIVATE_KEY_PATH missing/invalid in .env"
        )

    # Standard JWT payload required by GitHub
    payload = {
        # Issued at time, 60 seconds in the past to allow for clock drift
        'iat': int(time.time()) - 60,
        # JWT expiration time (10 minute maximum)
        'exp': int(time.time()) + (10 * 60),
        # GitHub App's identifier
        'iss': app_id
    }

    # Sign the JWT using the RS256 algorithm and the private key
    try:
        encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")
        return encoded_jwt
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate JWT: {str(e)}")


# ── Step 2: Get Installation Access Token ────────────────────────────
async def get_installation_access_token(installation_id: str) -> str:
    """
    Exchanges the App JWT for a short-lived installation access token
    which can be used to query repositories associated with this installation.
    """
    app_jwt = generate_app_jwt()

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github.v3+json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers)
        
    if response.status_code != 201:
        raise HTTPException(
            status_code=response.status_code, 
            detail=f"Failed to get installation token: {response.text}"
        )

    data = response.json()
    return data["token"]
