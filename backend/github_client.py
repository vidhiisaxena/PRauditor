import httpx
from backend.config import GITHUB_PERSONAL_TOKEN

def fetch_diff(repo: str, pr_number: int) -> str:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {GITHUB_PERSONAL_TOKEN}",
        "Accept": "application/vnd.github.v3.diff",
    }

    with httpx.Client(timeout=15) as client:
        r = client.get(url, headers=headers)
        r.raise_for_status()
        return r.text
