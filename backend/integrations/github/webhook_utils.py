import hmac
import hashlib
from typing import Optional

from backend.core.config import GITHUB_WEBHOOK_SECRET


def check_signature(signature: Optional[str], payload: bytes) -> bool:
    """
    Validate a GitHub webhook signature. Returns True if valid.
    """
    if not GITHUB_WEBHOOK_SECRET:
        from backend.core.config import ENV
        if ENV != "production":
            return True
        return False

    if not signature or "=" not in signature:
        return False

    algo, sent_sig = signature.split("=", 1)
    if algo != "sha256":
        return False

    expected = hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(sent_sig, expected)
