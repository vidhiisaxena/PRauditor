import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user, get_db
from backend.core.config import (
    AUTH_COOKIE_NAME,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    FRONTEND_URL,
    GITHUB_CLIENT_ID,
    JWT_EXPIRE_MINUTES,
)
from backend.schemas import UserOut
from backend.services import github_oauth, user_service
from backend.services.jwt_service import create_access_token, decode_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

STATE_COOKIE = "oauth_state"


@router.get("/github/login")
def github_login():
    """Redirect the user to GitHub's consent screen. Frontend never builds this URL."""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(500, "GitHub OAuth is not configured")

    state = secrets.token_urlsafe(32)
    response = RedirectResponse(github_oauth.build_authorize_url(state), status_code=302)
    # Short-lived, HttpOnly state cookie for CSRF protection on the callback.
    response.set_cookie(
        STATE_COOKIE,
        state,
        max_age=600,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )
    return response


@router.get("/github/callback")
def github_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    db: Session = Depends(get_db),
):
    """Exchange the code, load the GitHub user, persist them, set the session cookie."""
    if not code:
        raise HTTPException(400, "Missing authorization code")

    # CSRF: the returned state must match the one we issued. On any mismatch,
    # reject with 403 and clear the state cookie so it can't be reused.
    expected = request.cookies.get(STATE_COOKIE)
    if not state or not expected or not secrets.compare_digest(state, expected):
        rejected = JSONResponse({"detail": "Invalid OAuth state"}, status_code=403)
        rejected.delete_cookie(STATE_COOKIE, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE)
        return rejected

    try:
        token = github_oauth.exchange_code_for_token(code)
        profile = github_oauth.fetch_github_user(token)
        email = github_oauth.fetch_primary_email(token)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"GitHub OAuth failed: {e}")

    user = user_service.upsert_user_from_github(db, profile, email)
    jwt_token = create_access_token(user.id)

    response = RedirectResponse(f"{FRONTEND_URL}/dashboard", status_code=302)
    response.set_cookie(
        AUTH_COOKIE_NAME,
        jwt_token,
        max_age=JWT_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )
    response.delete_cookie(STATE_COOKIE)
    return response


@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)):
    """Return the currently signed-in user (used by the dashboard on load)."""
    return current_user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        AUTH_COOKIE_NAME, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE
    )
    return {"ok": True}


@router.get("/status")
def status(request: Request, db: Session = Depends(get_db)):
    """Lightweight check for route guards — never raises."""
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        return {"authenticated": False}
    payload = decode_access_token(token)
    if not payload:
        return {"authenticated": False}
    user = user_service.get_user_by_id(db, payload.get("user_id"))
    if not user:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "avatar_url": user.avatar_url,
        },
    }
