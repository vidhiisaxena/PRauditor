from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask
import logging
import fastapi

from backend.api.deps import get_current_user, get_current_user_optional, get_db
from backend.core.config import FRONTEND_URL
from backend.core.database import SessionLocal
from backend.schemas.installation import InstallationStatusOut, RepositorySummaryOut
from backend.services import github_app, installation_service, repository_service

router = APIRouter(prefix="/api", tags=["installations"])
logger=logging.getLogger(__name__)


def _sync_installation_in_background(github_installation_id: int) -> None:
    # Runs after the setup redirect is sent.
    try:
        repository_service.sync_installation_repositories(github_installation_id)
    except Exception:
        pass  # best-effort; user can hit POST /api/installations/sync


@router.get("/installations", response_model=InstallationStatusOut)
def installation_status(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    # Whether the signed-in user has installed PRAuditor. DB-only, no GitHub call.
    installs = installation_service.get_user_installations(db, current_user.id)
    return {"installed": len(installs) > 0, "installations": installs}


@router.get("/installations/repositories", response_model=list[RepositorySummaryOut])
def list_repositories(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    return repository_service.get_user_repositories(db, current_user.id)


@router.post("/installations/sync")
def sync_repositories(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    #Manually re-sync repositories for the user's installation(s).
    installs = installation_service.get_user_installations(db, current_user.id)
    if not installs:
        raise HTTPException(404, "No installation found for this user")

    total = 0
    for inst in installs:
        total += len(repository_service.sync_installation_repositories(inst.github_installation_id))
    return {"synced": True, "repositories": total}


@router.delete("/installations/{github_installation_id}")
def disconnect_installation(
    github_installation_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    '''
    Disconnect an installation the user owns: deactivate its repositories and
    remove our installation record. (The GitHub-side uninstall is separate;
    this removes PRAuditor's link to it.)
    '''
    removed = installation_service.delete_installation(
        db, user_id=current_user.id, github_installation_id=github_installation_id
    )
    if not removed:
        raise HTTPException(404, "Installation not found for this user")
    return {"disconnected": True}


@router.get("/github-app/setup")
def github_app_setup(
    request: Request,
    installation_id: int | None = None,
    setup_action: str | None = None,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    '''
    GitHub's App "Setup URL" callback. GitHub redirects here after install with
    ?installation_id=. We validate it, link it to the logged-in user, do an
    initial repo sync, then redirect back to the dashboard.
    '''
    if current_user is None:
        # Not logged in in this browser — send them to log in first.
        return RedirectResponse(f"{FRONTEND_URL}/login", status_code=302)

    if not installation_id:
        return RedirectResponse(
            f"{FRONTEND_URL}/dashboard?installed=error", status_code=302
        )

    try:
        logger.info(
        "GitHub App setup started: installation_id=%s user_id=%s",
        installation_id,
        current_user.id,
        )

        gh_inst = github_app.get_installation(installation_id)

        logger.info(
            "GitHub App installation validated: installation_id=%s account=%s",
            installation_id,
            gh_inst.get("account", {}).get("login"),
        )
        
    except Exception as e:
        logger.exception(
        "GitHub App installation validation FAILED: installation_id=%s user_id=%s",
        installation_id,
        current_user.id,
        )
        return RedirectResponse(
            f"{FRONTEND_URL}/dashboard?installed=error",
            status_code=302
        )

    account = gh_inst.get("account") or {}
    inst = installation_service.upsert_installation(
        db,
        github_installation_id=installation_id,
        user_id=current_user.id,
        account_login=account.get("login"),
        account_type=account.get("type"),
        target_type=gh_inst.get("target_type"),
    )

    # Sync repositories in the BACKGROUND so the redirect is instant even for
    # accounts with hundreds of repos. The dashboard reads them from
    # GET /api/installations/repositories (and can poll briefly if empty).
    return RedirectResponse(
        f"{FRONTEND_URL}/dashboard?installed=true",
        status_code=302,
        background=BackgroundTask(
            _sync_installation_in_background, inst.github_installation_id
        ),
    )
