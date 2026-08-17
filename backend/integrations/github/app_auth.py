import time
import logging
import httpx
import jwt

from backend.core.config import GITHUB_APP_ID, GITHUB_PRIVATE_KEY

logger=logging.getLogger(__name__)

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
    '''
    Exchange the app JWT for an installation access token.
    '''
    logger.info(
        "Fetching GitHub installation token: installation_id=%s",
        installation_id,
    )

    try:
        jwt_token = generate_jwt()
        logger.info("GitHub App JWT generated successfully")
    except Exception as e:
        logger.exception("Failed to generate GitHub App JWT")
        raise ValueError(f"Failed to generate JWT token: {e}") from e

    url = (
        f"https://api.github.com/app/installations/"
        f"{installation_id}/access_tokens"
    )

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        r = httpx.post(url, headers=headers, timeout=15)
    except Exception as e:
        logger.exception("GitHub API connection failed")
        raise ValueError(f"Failed to connect to GitHub API: {e}") from e

    logger.info(
        "GitHub installation token response: status=%s installation_id=%s",
        r.status_code,
        installation_id,
    )

    if r.status_code >= 400:
        logger.error(
            "GitHub installation token failed: status=%s body=%s",
            r.status_code,
            r.text,
        )

    r.raise_for_status()

    response_data = r.json()

    if "token" not in response_data:
        raise ValueError(
            f"GitHub API did not return a token. Response: {response_data}"
        )

    logger.info(
        "Successfully obtained installation token for installation_id=%s",
        installation_id,
    )

    return response_data["token"]