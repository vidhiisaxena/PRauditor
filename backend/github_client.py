import time
import httpx
import jwt

from backend.config import GITHUB_APP_ID, GITHUB_PRIVATE_KEY


def generate_jwt() -> str:
    """
    Create a short-lived JWT for GitHub App authentication.
    """
    if not GITHUB_APP_ID:
        raise ValueError("GITHUB_APP_ID is not configured")
    
    if not GITHUB_PRIVATE_KEY:
        raise ValueError("GITHUB_PRIVATE_KEY is not configured")
    
    # Ensure APP_ID is a string (GitHub expects it as a string in JWT)
    app_id = str(GITHUB_APP_ID).strip()
    if not app_id:
        raise ValueError("GITHUB_APP_ID is empty")
    
    now = int(time.time())
    # GitHub allows JWT to be valid for max 10 minutes from iat
    # Set iat to 30 seconds in the past to account for clock skew
    # Set exp to exactly 10 minutes from iat (not from now)
    iat = now - 30
    exp = iat + (10 * 60)  # 10 minutes from iat
    
    payload = {
        "iat": iat,
        "exp": exp,
        "iss": app_id,
    }
    
    try:
        return jwt.encode(payload, GITHUB_PRIVATE_KEY, algorithm="RS256")
    except Exception as e:
        raise ValueError(f"Failed to generate JWT: {str(e)}") from e


def get_installation_token(installation_id: int) -> str:
    """
    Exchange app JWT for an installation access token.
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
    
    # Check for 401 before calling raise_for_status
    if r.status_code == 401:
        try:
            error_detail = r.json()
        except:
            error_detail = r.text
        
        error_msg = (
            f"GitHub API authentication failed (401 Unauthorized).\n"
            f"Installation ID: {installation_id}\n"
            f"App ID: {GITHUB_APP_ID}\n"
            f"Private Key loaded: {'Yes' if GITHUB_PRIVATE_KEY else 'No'}\n"
            f"GitHub API Response: {error_detail}\n"
            f"Please verify:\n"
            f"  1. GITHUB_APP_ID matches your GitHub App ID\n"
            f"  2. GITHUB_PRIVATE_KEY is the correct private key for this app\n"
            f"  3. Installation {installation_id} belongs to this app"
        )
        raise ValueError(error_msg)
    
    try:
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        error_msg = f"GitHub API error ({r.status_code}): {r.text}"
        raise ValueError(error_msg) from e
    
    try:
        response_data = r.json()
    except Exception as e:
        raise ValueError(f"Failed to parse GitHub API response: {str(e)}") from e
    
    if "token" not in response_data:
        raise ValueError(f"GitHub API did not return a token. Response: {response_data}")
    
    return response_data["token"]


def fetch_pr_diff(repo_full: str, pr_number: int, installation_id: int) -> str:
    """
    Fetch unified diff for a PR using installation token.
    """
    token = get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{repo_full}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.diff",
    }
    r = httpx.get(url, headers=headers)
    r.raise_for_status()
    return r.text


def post_pr_comment(repo_full: str, pr_number: int, body: str, installation_id: int):
    """
    Post a PR review comment using installation token.
    """
    token = get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{repo_full}/pulls/{pr_number}/reviews"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"body": body, "event": "COMMENT"}
    r = httpx.post(url, json=payload, headers=headers)
    r.raise_for_status()
