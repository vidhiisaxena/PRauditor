#Create and verify the session JWT stored in the auth cookie.

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from backend.core.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET


def create_access_token(user_id: int) -> str:
    # Keep the payload minimal: the user id is enough to load everything else.
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Return the decoded payload, or None if the token is invalid/expired."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
