import time

import httpx
import jwt

from backend.core.config import GITHUB_APP_ID, GITHUB_PRIVATE_KEY


def generate_jwt() -> str:
    """
    Create a short-lived JWT for GitHub App authentication.
    """
    if not GITHUB_APP_ID:
        raise ValueError("GITHUB_APP_ID is not configured")

    if not GITHUB_PRIVATE_KEY:
        raise ValueError("GITHUB_PRIVATE_KEY is not configured")

    # GitHub expects the App ID as a string in the JWT.
    app_id = str(GITHUB_APP_ID).strip()
    if not app_id:
        raise ValueError("GITHUB_APP_ID is empty")

    now = int(time.time())
    # JWT valid for max 10 minutes; back-date iat 30s to absorb clock skew.
    iat = now - 30
    exp = iat + (10 * 60)

    payload = {"iat": iat, "exp": exp, "iss": app_id}

    try:
        return jwt.encode(payload, GITHUB_PRIVATE_KEY, algorithm="RS256")
    except Exception as e:
        raise ValueError(f"Failed to generate JWT: {str(e)}") from e


def get_installation_token(installation_id: int) -> str:
    """
    Exchange the app JWT for an installation access token.
    """
    try:
        jwt_token = generate_jwt()
    except Exception as e:
        raise ValueError(f"Failed to generate JWT token: {str(e)}") from e

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }

    try:
        r = httpx.post(url, headers=headers)
    except Exception as e:
        raise ValueError(f"Failed to connect to GitHub API: {str(e)}") from e

    if r.status_code == 401:
        try:
            error_detail = r.json()
        except Exception:
            error_detail = r.text
        raise ValueError(
            "GitHub API authentication failed (401 Unauthorized).\n"
            f"Installation ID: {installation_id}\n"
            f"App ID: {GITHUB_APP_ID}\n"
            f"Private Key loaded: {'Yes' if GITHUB_PRIVATE_KEY else 'No'}\n"
            f"GitHub API Response: {error_detail}\n"
            "Verify GITHUB_APP_ID, GITHUB_PRIVATE_KEY, and that the installation "
            "belongs to this app."
        )

    try:
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise ValueError(f"GitHub API error ({r.status_code}): {r.text}") from e

    try:
        response_data = r.json()
    except Exception as e:
        raise ValueError(f"Failed to parse GitHub API response: {str(e)}") from e

    if "token" not in response_data:
        raise ValueError(f"GitHub API did not return a token. Response: {response_data}")

    return response_data["token"]
