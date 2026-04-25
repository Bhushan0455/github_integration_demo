"""
routers/webhooks.py — GitHub Webhook Handler
=============================================
This file handles incoming webhooks from GitHub.

HOW IT WORKS:
1. When code is pushed to a repository where your GitHub App is installed,
   GitHub immediately sends a POST request to this endpoint with details
   about the push.
2. SECURITY FIRST: We MUST verify the signature (X-Hub-Signature-256)
   to ensure the request actually came from GitHub and not an attacker.
   We do this using the GITHUB_WEBHOOK_SECRET.
3. We parse the payload to extract the repo name, commit SHA, and changed files.
4. DEPENDENCY DETECTION: We check if any changed files are known package configs
   (like package.json). If so, we set `should_scan=True` for Phase 5.
5. We save the event to the database and print a clean terminal UI.
"""

import os
import hmac
import hashlib
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from colorama import init, Fore, Style

from database import get_db
from models import WebhookEvent

# Initialize colorama for colored terminal output on Windows
init(autoreset=True)

router = APIRouter(prefix="/webhook", tags=["Webhooks"])

# The secret phrase configured in your GitHub App settings
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

# Dependency files we care about tracking for vulnerabilities
DEPENDENCY_FILES = {"package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"}


# ════════════════════════════════════════════════════════════════════
# HELPER: Verify Webhook Signature
# ════════════════════════════════════════════════════════════════════
def verify_signature(payload_body: bytes, signature_header: str) -> bool:
    """
    Verifies that the webhook really came from GitHub using the HMAC-SHA256 hash.
    It takes the raw request body, hashes it using our secret string, 
    and checks if it matches the signature GitHub sent in the headers.
    """
    if not WEBHOOK_SECRET:
        # If no secret is configured, we can't be secure. Reject all.
        print(f"{Fore.RED}ERROR: GITHUB_WEBHOOK_SECRET is not set in .env!{Style.RESET_ALL}")
        return False
        
    if not signature_header:
        return False

    # Create our own HMAC-SHA256 signature using the secret and the request body
    hash_obj = hmac.new(WEBHOOK_SECRET.encode("utf-8"), payload_body, hashlib.sha256)
    expected_signature = "sha256=" + hash_obj.hexdigest()

    # Compare our generated signature with the one GitHub provided.
    # We use hmac.compare_digest instead of `==` to prevent timing attacks.
    return hmac.compare_digest(expected_signature, signature_header)


# ════════════════════════════════════════════════════════════════════
# ROUTE: Receive GitHub Webhook
# ════════════════════════════════════════════════════════════════════
@router.post("/github")
async def handle_github_webhook(request: Request, db: Session = Depends(get_db)):
    """
    The main webhook receiver endpoint.
    GitHub must be able to reach this URL over the public internet (use ngrok).
    """

    # 1. Verify the signature securely
    signature_header = request.headers.get("X-Hub-Signature-256", "")
    payload_body = await request.body()  # We need the RAW bytes to verify the hash

    if not verify_signature(payload_body, signature_header):
        raise HTTPException(status_code=403, detail="Invalid webhook signature!")

    # 2. Parse the payload JSON and event type
    event_type = request.headers.get("X-GitHub-Event", "unknown")
    try:
        payload = json.loads(payload_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # We only care about user "push" events for this demo (code being committed)
    if event_type == "push":
        
        # Extract relevant fields
        repo_name = payload.get("repository", {}).get("full_name", "unknown")
        # In a push, 'head_commit' represents the latest commit made
        head_commit = payload.get("head_commit")
        
        if head_commit:
            commit_sha = head_commit.get("id", "none")
            
            # Extract all files that were added, modified, or removed
            added = head_commit.get("added", [])
            modified = head_commit.get("modified", [])
            removed = head_commit.get("removed", [])
            
            all_changed_files = added + modified + removed
            
            # DEPENDENCY DETECTION:
            # Check if any of the changed files are in our DEPENDENCY_FILES list
            # We just check the end of the filename to handle paths (e.g. backend/package.json)
            should_scan = any(
                any(filename.endswith(dep_file) for dep_file in DEPENDENCY_FILES)
                for filename in all_changed_files
            )

            # Save the event to our database
            event_record = WebhookEvent(
                event_type="push",
                repo_name=repo_name,
                commit_sha=commit_sha,
                changed_files=json.dumps(all_changed_files),
                should_scan=should_scan
            )
            db.add(event_record)
            db.commit()

            # Format the output for the terminal
            print_terminal_ui(repo_name, commit_sha, all_changed_files, should_scan)

    # Return 200 OK so GitHub knows we received it successfully
    return {"status": "ok"}


# ════════════════════════════════════════════════════════════════════
# HELPER: Print Clean Terminal UI
# ════════════════════════════════════════════════════════════════════
def print_terminal_ui(repo_name: str, commit_sha: str, changed_files: list, should_scan: bool):
    """
    Renders the beautiful terminal output asked for in the plan.
    """
    short_sha = commit_sha[:7] if commit_sha else "none"
    
    print("\n" + Fore.CYAN + "═" * 47)
    print(Fore.YELLOW + Style.BRIGHT + "🔔 PUSH EVENT RECEIVED")
    print(Fore.CYAN + "─" * 47)
    print(f"{Style.BRIGHT}📦 Repository : {Style.NORMAL}{repo_name}")
    print(f"{Style.BRIGHT}🔑 Commit SHA : {Style.NORMAL}{short_sha}")
    print(f"{Style.BRIGHT}📝 Changed Files:")
    
    if not changed_files:
        print("   " + Fore.LIGHTBLACK_EX + "(No files changed)")
    else:
        # Show top 5 files, then summarize if too many
        for f in changed_files[:5]:
            # Highlight dependency files in output
            if any(f.endswith(d) for d in DEPENDENCY_FILES):
                print(f"   • {f} " + Fore.MAGENTA + "← dependency file")
            else:
                print(f"   • {f}")
        if len(changed_files) > 5:
            print(f"   " + Fore.LIGHTBLACK_EX + f"...and {len(changed_files) - 5} more")

    # Dependency detection badge
    if should_scan:
        print(f"🔍 Should Scan : " + Fore.GREEN + "✅ Yes (dependency files changed)")
    else:
        print(f"🔍 Should Scan : " + Fore.WHITE + "❌ No")
        
    print(Fore.CYAN + "═" * 47 + "\n" + Style.RESET_ALL)

# ════════════════════════════════════════════════════════════════════
# ROUTE: Get Recent Webhooks
# ════════════════════════════════════════════════════════════════════
@router.get("/recent")
async def get_recent_webhooks(request: Request, db: Session = Depends(get_db)):
    """
    Used by the frontend Dashboard to display recently received webhooks.
    """
    events = db.query(WebhookEvent).order_by(WebhookEvent.received_at.desc()).limit(10).all()
    
    return [
        {
            "id": event.id,
            "event_type": event.event_type,
            "repo_name": event.repo_name,
            "commit_sha": event.commit_sha[:7] if event.commit_sha else "none",
            "changed_files": json.loads(event.changed_files) if event.changed_files else [],
            "should_scan": event.should_scan
        }
        for event in events
    ]
