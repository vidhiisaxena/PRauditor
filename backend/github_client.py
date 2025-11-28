import httpx
from backend.config import GITHUB_PERSONAL_TOKEN

BASE = "https://api.github.com"


def fetch_pr_diff(repo_full_name: str, pr_number: int) -> str:
    """
    Fetch unified diff for a pull request.
    """
    url = f"{BASE}/repos/{repo_full_name}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff"
    }

    with httpx.Client(timeout=20) as client:
        r = client.get(url, headers=headers)
        r.raise_for_status()
        return r.text


def post_pr_comment(repo_full_name: str, pr_number: int, body: str) -> None:
    """
    Post a review comment (not line-level) to a PR.
    """
    url = f"{BASE}/repos/{repo_full_name}/pulls/{pr_number}/reviews"

    headers = {
        "Authorization": f"token {GITHUB_PERSONAL_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    payload = {
        "body": body,
        "event": "COMMENT"
    }

    with httpx.Client(timeout=20) as client:
        r = client.post(url, json=payload, headers=headers)
        r.raise_for_status()
