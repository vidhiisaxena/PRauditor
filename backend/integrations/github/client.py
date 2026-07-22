import httpx

from backend.integrations.github.app_auth import get_installation_token


def fetch_pr_diff(repo_full: str, pr_number: int, installation_id: int) -> str:
    """
    Fetch the unified diff for a PR using an installation token.
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
    Post a PR review comment using an installation token.
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
