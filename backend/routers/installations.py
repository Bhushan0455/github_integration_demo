"""
routers/installations.py — GitHub App Installation Routes
==========================================================
These routes handle what happens after a user installs the GitHub App.

1. User selects repositories and installs the app on GitHub.
2. GitHub redirects the user to our frontend callback URL with an `installation_id`.
3. Frontend calls `POST /github/installations/save` with this `installation_id`.
4. Our backend uses this `installation_id` to fetch the selected repos and saves them.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
import httpx
import os

from database import get_db
from models import User, Installation, Repository
from github_jwt import get_installation_access_token

router = APIRouter(prefix="/github/installations", tags=["Installations"])

# ── Helper to authenticate user from token ────────────────────────
def get_current_user(request: Request, db: Session) -> User:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = auth_header.split(" ")[1]
    
    user = db.query(User).filter(User.access_token == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user token")
    return user

# ── Pydantic Request Model ────────────────────────────────────────
class InstallSaveRequest(BaseModel):
    installation_id: int

# ════════════════════════════════════════════════════════════════════
# ROUTE: Save Installation and Fetch Repositories
# ════════════════════════════════════════════════════════════════════
@router.post("/save")
async def save_installation(req: InstallSaveRequest, request: Request, db: Session = Depends(get_db)):
    """
    After the user installs the GitHub App, they are redirected back to the frontend
    with an `installation_id`. The frontend sends that ID here.
    """
    user = get_current_user(request, db)
    installation_id = req.installation_id
    app_slug = os.getenv("GITHUB_APP_SLUG", "github-integration-demo")

    # 1. Fetch an installation access token using our App JWT logic
    install_token = await get_installation_access_token(installation_id)

    # 2. Use the installation token to fetch the repositories the user selected
    url = "https://api.github.com/installation/repositories"
    headers = {
        "Authorization": f"Bearer {install_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, 
            detail=f"Failed to fetch repositories: {response.text}"
        )

    repos_data = response.json().get("repositories", [])

    # 3. Save or update the installation record in our DB
    installation = db.query(Installation).filter(Installation.installation_id == installation_id).first()
    if not installation:
        installation = Installation(
            installation_id=installation_id,
            user_id=user.id,
            app_slug=app_slug
        )
        db.add(installation)
        db.commit()
        db.refresh(installation)

    # 4. Save the selected repositories
    # To keep it simple, we delete old repos tied to this installation and add the fresh list
    db.query(Repository).filter(Repository.installation_id == installation.id).delete()
    
    for repo in repos_data:
        new_repo = Repository(
            installation_id=installation.id,
            full_name=repo["full_name"],
            github_repo_id=repo["id"]
        )
        db.add(new_repo)

    db.commit()

    return {"status": "success", "message": f"Saved {len(repos_data)} repositories."}

# ════════════════════════════════════════════════════════════════════
# ROUTE: List Installations
# ════════════════════════════════════════════════════════════════════
@router.get("")
async def get_installations(request: Request, db: Session = Depends(get_db)):
    """
    Returns all GitHub App installations and associated repositories for the logged-in user.
    """
    user = get_current_user(request, db)
    
    installations = db.query(Installation).filter(Installation.user_id == user.id).all()
    
    result = []
    for inst in installations:
        repos = db.query(Repository).filter(Repository.installation_id == inst.id).all()
        result.append({
            "id": inst.id,
            "installation_id": inst.installation_id,
            "app_slug": inst.app_slug,
            "repositories": [
                {"id": r.id, "full_name": r.full_name} for r in repos
            ]
        })

    return result
