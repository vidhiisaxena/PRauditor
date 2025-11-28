import hmac
import hashlib
from typing import Optional

from backend.config import GITHUB_WEBHOOK_SECRET


def check_signature(signature: Optional[str], payload: bytes) -> bool:

    # If secret not set, don't enforce validation (dev mode)
    if not GITHUB_WEBHOOK_SECRET:
        return True

    if not signature:
        return False

    # Signature comes in format: sha256=abcdef...
    if "=" not in signature:
        return False

    algo, sent_sig = signature.split("=", 1)

    if algo != "sha256":
        return False

    expected_sig = hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(sent_sig, expected_sig)
