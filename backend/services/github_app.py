"""
GitHub App service — a thin orchestration layer over the existing low-level
GitHub App auth in `integrations/github/app_auth.py`. It does NOT reimplement
JWT signing or token exchange; it reuses them and adds the two calls the
onboarding flow needs (fetch an installation, list its repositories).
"""

from typing import List

import httpx

# REUSED: existing app-JWT + installation-token implementation.
from backend.integrations.github.app_auth import generate_jwt, get_installation_token

GITHUB_API = "https://api.github.com"


def create_app_jwt() -> str:
    """App-level JWT (RS256). Delegates to the existing implementation."""
    return generate_jwt()


def get_installation_access_token(installation_id: int) -> str:
    """Installation access token. Delegates to the existing implementation."""
    return get_installation_token(installation_id)


def get_installation(installation_id: int) -> dict:
    """
    GET /app/installations/{id} using the app JWT — used to validate an
    installation and read its account (login / type) during setup.
    """
    headers = {
        "Authorization": f"Bearer {create_app_jwt()}",
        "Accept": "application/vnd.github+json",
    }
    r = httpx.get(
        f"{GITHUB_API}/app/installations/{installation_id}", headers=headers, timeout=15
    )
    r.raise_for_status()
    return r.json()


def list_installation_repositories(installation_id: int) -> List[dict]:
    """
    All repositories the installation can access (paginated), using an
    installation token. Returns the raw GitHub repo objects.
    """
    headers = {
        "Authorization": f"token {get_installation_access_token(installation_id)}",
        "Accept": "application/vnd.github+json",
    }
    repositories: List[dict] = []
    page = 1
    while True:
        r = httpx.get(
            f"{GITHUB_API}/installation/repositories",
            headers=headers,
            params={"per_page": 100, "page": page},
            timeout=20,
        )
        r.raise_for_status()
        batch = r.json().get("repositories", [])
        repositories.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repositories
