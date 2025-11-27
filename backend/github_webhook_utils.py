import hmac
import hashlib
from fastapi import HTTPException

from backend.config import GITHUB_WEBHOOK_SECRET

def check_signature(signature: str | None, payload: bytes):
    if not GITHUB_WEBHOOK_SECRET:
        return  # Skip if not configured

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    try:
        _, sent = signature.split("=")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature header")

    expected = hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(sent, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")
