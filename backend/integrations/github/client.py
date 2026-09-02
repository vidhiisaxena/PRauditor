from typing import Optional, Dict, Any
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
    r = httpx.get(url, headers=headers, timeout=30.0)
    r.raise_for_status()
    return r.text


def fetch_pr_details(repo_full: str, pr_number: int, installation_id: int) -> Dict[str, Any]:
    """
    Fetch PR metadata details (title, description, base_sha, head_sha) from GitHub API.
    """
    token = get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{repo_full}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    r = httpx.get(url, headers=headers, timeout=30.0)
    r.raise_for_status()
    data = r.json()

    return {
        "title": data.get("title", ""),
        "description": data.get("body") or "",
        "base_sha": data.get("base", {}).get("sha", ""),
        "head_sha": data.get("head", {}).get("sha", ""),
    }


def fetch_file_content_at_sha(repo_full: str, path: str, sha: str, installation_id: int) -> Optional[str]:
    """
    Fetch raw file content at a specific commit SHA via GitHub API.
    """
    if not sha or not path:
        return None

    token = get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{repo_full}/contents/{path}?ref={sha}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.raw+json",
    }
    r = httpx.get(url, headers=headers, timeout=30.0)
    if r.status_code == 404:
        return None
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
    r = httpx.post(url, json=payload, headers=headers, timeout=30.0)
    r.raise_for_status()


def get_installation_repositories(installation_id):
    token = get_installation_token(installation_id)
    url = f"https://api.github.com/installation/repositories"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    r = httpx.get(url, headers=headers, timeout=30.0)
    r.raise_for_status()
    return r.json().get("repositories", [])


def fetch_repository_prs(repo_full, installation_id):
    token = get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{repo_full}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    r = httpx.get(url, headers=headers, timeout=30.0)
    r.raise_for_status()
    return r.json()
