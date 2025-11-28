import jwt
import time
import httpx
from pathlib import Path
from backend.config import GITHUB_APP_ID, GITHUB_INSTALLATION_ID, GITHUB_PRIVATE_KEY

def generate_jwt():
    private_key = Path(GITHUB_PRIVATE_KEY).read_text()

    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + (10 * 60),
        "iss": GITHUB_APP_ID,
    }

    return jwt.encode(payload, private_key, algorithm="RS256")


def get_installation_token():
    jwt_token = generate_jwt()

    url = f"https://api.github.com/app/installations/{GITHUB_INSTALLATION_ID}/access_tokens"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }

    r = httpx.post(url, headers=headers)
    r.raise_for_status()

    return r.json()["token"]
