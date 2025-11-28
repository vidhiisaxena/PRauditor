import time
import jwt
import httpx
from backend.config import (
    GITHUB_APP_ID,
    GITHUB_PRIVATE_KEY,
    GITHUB_INSTALLATION_ID
)
from backend.github_app_auth import get_installation_token


BASE = "https://api.github.com"


def generate_jwt():
    """Create a JWT signed by your GitHub App private key."""
    now = int(time.time())
    payload = {
        "iat": now,
        "exp": now + 540,  
        "iss": GITHUB_APP_ID,
    }
    return jwt.encode(payload, GITHUB_PRIVATE_KEY, algorithm="RS256")


def get_installation_token():
    """Exchange the JWT for an installation access token."""
    jwt_token = generate_jwt()

    url = f"{BASE}/app/installations/{GITHUB_INSTALLATION_ID}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }

    r = httpx.post(url, headers=headers)
    print("INSTALL TOKEN:", r.status_code, r.text)
    r.raise_for_status()

    return r.json()["token"]

def fetch_pr_diff(repo_full_name: str, pr_number: int) -> str:
    token = get_installation_token()

    url = f"{BASE}/repos/{repo_full_name}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff",
    }

    with httpx.Client(timeout=20) as client:
        r = client.get(url, headers=headers)
        r.raise_for_status()
        return r.text
    
    
def post_pr_comment(repo_full, pr_number, body):
    """Post a comment on a PR using the GitHub App installation token."""
    token = get_installation_token()

    url = f"{BASE}/repos/{repo_full}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    payload = {"body": body}

    r = httpx.post(url, json=payload, headers=headers)
    print("COMMENT RESPONSE:", r.status_code, r.text)
    r.raise_for_status()
