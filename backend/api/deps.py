from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.core.config import AUTH_COOKIE_NAME
from backend.core.database import get_db
from backend.services import user_service
from backend.services.jwt_service import decode_access_token


def get_current_user(request: Request, db: Session = Depends(get_db)):
    #Resolve the signed-in user from the auth cookie, or 401.
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")

    user = user_service.get_user_by_id(db, payload.get("user_id"))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    return user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)):
    """Like get_current_user but returns None instead of raising.

    Used by redirect endpoints (e.g. the GitHub App setup callback) that must
    not 401 the browser mid-redirect.
    """
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    return user_service.get_user_by_id(db, payload.get("user_id"))


__all__ = ["get_db", "get_current_user", "get_current_user_optional"]
