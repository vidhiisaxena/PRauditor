"""GitHub OAuth: build the authorize URL and exchange the code for a profile."""

from typing import Optional
from urllib.parse import urlencode

import httpx

from backend.core.config import (
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    GITHUB_OAUTH_CALLBACK_URL,
    GITHUB_OAUTH_SCOPE,
)

AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
API_BASE = "https://api.github.com"


def build_authorize_url(state: str) -> str:
    """The GitHub consent-screen URL to redirect the user to."""
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_OAUTH_CALLBACK_URL,
        "scope": GITHUB_OAUTH_SCOPE,
        "state": state,
        "allow_signup": "true",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> str:
    """Exchange the OAuth code for a user access token (uses the client secret)."""
    resp = httpx.post(
        TOKEN_URL,
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": GITHUB_OAUTH_CALLBACK_URL,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise ValueError(f"GitHub did not return an access token: {data}")
    return token


def fetch_github_user(token: str) -> dict:
    """Fetch the authenticated user's profile (login, id, name, avatar_url)."""
    resp = httpx.get(f"{API_BASE}/user", headers=_auth_headers(token), timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_primary_email(token: str) -> Optional[str]:
    """Return the user's primary, verified email if available."""
    resp = httpx.get(f"{API_BASE}/user/emails", headers=_auth_headers(token), timeout=15)
    if resp.status_code != 200:
        return None
    emails = resp.json()
    for e in emails:
        if e.get("primary") and e.get("verified"):
            return e.get("email")
    return emails[0].get("email") if emails else None


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
