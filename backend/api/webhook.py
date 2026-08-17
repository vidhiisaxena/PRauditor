import json
import logging

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend import models
from backend.core.config import GITHUB_INSTALLATION_ID
from backend.integrations.github.webhook_utils import check_signature
from backend.services.review_service import run_and_store_review

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["webhook"])


@router.post("/github/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    delivery_id = request.headers.get("X-GitHub-Delivery", "unknown")
    logger.info(f"[Webhook] Received GitHub webhook. Delivery ID: {delivery_id}")
    
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    content_type = request.headers.get("content-type", "")

    # 1. Parse payload
    if content_type.startswith("application/x-www-form-urlencoded"):
        form = await request.form()
        payload = form.get("payload")
        if not payload:
            logger.error(f"[Webhook {delivery_id}] Missing payload in form data")
            raise HTTPException(400, "Missing payload")
        try:
            data = json.loads(payload)
        except Exception as e:
            logger.error(f"[Webhook {delivery_id}] Failed to parse JSON in form payload: {e}")
            raise HTTPException(400, "Invalid JSON inside form payload")
    else:
        try:
            data = json.loads(raw_body.decode())
        except Exception as e:
            logger.error(f"[Webhook {delivery_id}] Failed to parse JSON body: {e}")
            raise HTTPException(400, "Invalid JSON body")

    event = request.headers.get("X-GitHub-Event")
    action = data.get("action")
    logger.info(f"[Webhook {delivery_id}] GitHub event: {event}, action: {action}")

    # 2. Verify signature
    if not check_signature(signature, raw_body):
        logger.error(f"[Webhook {delivery_id}] Signature verification failed")
        raise HTTPException(401, "Invalid signature")

    if event == "ping":
        logger.info(f"[Webhook {delivery_id}] Ping event, responding OK")
        return {"ok": True}

    if event != "pull_request":
        logger.info(f"[Webhook {delivery_id}] Ignoring non-pull_request event: {event}")
        return {"ignored": True}

    if action not in ("opened", "reopened", "synchronize"):
        logger.info(f"[Webhook {delivery_id}] Ignoring pull_request action: {action}")
        return {"ignored": True}

    # Installation id: prefer the webhook payload, fall back to config.
    installation = data.get("installation")
    installation_id = installation.get("id") if isinstance(installation, dict) else None
    if not installation_id and GITHUB_INSTALLATION_ID:
        try:
            installation_id = int(GITHUB_INSTALLATION_ID)
            logger.info(f"[Webhook {delivery_id}] Using fallback GITHUB_INSTALLATION_ID: {installation_id}")
        except (ValueError, TypeError):
            installation_id = None
    if not installation_id:
        logger.error(f"[Webhook {delivery_id}] Installation ID not found in webhook or config")
        raise HTTPException(
            400,
            "Missing installation ID. Not found in webhook payload and "
            "GITHUB_INSTALLATION_ID not configured.",
        )

    repo_full = data.get("repository", {}).get("full_name")
    if not repo_full:
        logger.error(f"[Webhook {delivery_id}] Missing repository data")
        raise HTTPException(400, "Missing repository data in webhook payload")

    pr_info = data.get("pull_request")
    if not pr_info:
        logger.error(f"[Webhook {delivery_id}] Missing pull_request data")
        raise HTTPException(400, "Missing pull_request data in webhook payload")

    pr_number = pr_info.get("number")
    if not pr_number:
        logger.error(f"[Webhook {delivery_id}] Missing PR number")
        raise HTTPException(400, "Missing PR number in webhook payload")

    logger.info(f"[Webhook {delivery_id}] Processing PR: {repo_full}#{pr_number}, action: {action}, installation_id: {installation_id}")

    title = pr_info.get("title")
    state = pr_info.get("state")
    head_sha = pr_info.get("head", {}).get("sha")

    # Upsert repository. Match on the immutable GitHub repo id first (rename-safe),
    # falling back to full_name for rows created before we stored the id. Also
    # remember which installation owns it, so manual reruns work later.
    github_repo_id = data.get("repository", {}).get("id")

    repo = None
    if github_repo_id is not None:
        repo = (
            db.query(models.Repository)
            .filter(models.Repository.github_id == github_repo_id)
            .first()
        )
        if repo:
            logger.debug(f"[Webhook {delivery_id}] Found repository by github_id: {github_repo_id}")
    
    if repo is None:
        repo = (
            db.query(models.Repository)
            .filter(models.Repository.full_name == repo_full)
            .first()
        )
        if repo:
            logger.debug(f"[Webhook {delivery_id}] Found repository by full_name: {repo_full}")

    if repo is None:
        logger.info(f"[Webhook {delivery_id}] Creating new repository record: {repo_full}")
        repo = models.Repository(
            full_name=repo_full,
            installation_id=installation_id,
            github_id=github_repo_id,
        )
        db.add(repo)
    else:
        logger.debug(f"[Webhook {delivery_id}] Updating existing repository: {repo_full}")
        repo.full_name = repo_full  # keep name fresh if the repo was renamed
        repo.installation_id = installation_id
        if github_repo_id is not None:
            repo.github_id = github_repo_id
    
    db.commit()
    db.refresh(repo)
    logger.info(f"[Webhook {delivery_id}] Repository persisted: {repo.full_name} (id={repo.id}, installation_id={repo.installation_id})")

    # Upsert pull request
    pr = (
        db.query(models.PullRequest)
        .filter(
            models.PullRequest.repo_id == repo.id,
            models.PullRequest.pr_number == pr_number,
        )
        .first()
    )
    if not pr:
        logger.info(f"[Webhook {delivery_id}] Creating new PR record: {pr_number}")
        pr = models.PullRequest(
            repo_id=repo.id,
            pr_number=pr_number,
            title=title,
            state=state,
            head_sha=head_sha,
        )
        db.add(pr)
    else:
        logger.debug(f"[Webhook {delivery_id}] Updating existing PR: {pr_number}")
        pr.title = title
        pr.state = state
        pr.head_sha = head_sha
    
    db.commit()
    db.refresh(pr)
    logger.info(f"[Webhook {delivery_id}] PR persisted: {pr_number} (id={pr.id})")

    # Fetch diff → review → store issues → post comment
    try:
        logger.info(f"[Webhook {delivery_id}] Starting audit pipeline for {repo_full}#{pr_number}")
        issues = run_and_store_review(db, repo, pr, installation_id)
        logger.info(f"[Webhook {delivery_id}] Audit completed successfully. Found {len(issues)} issues")
        return JSONResponse({"reviewed": True, "issues": len(issues)})
    except ValueError as e:
        logger.error(f"[Webhook {delivery_id}] Failed to fetch PR diff: {e}")
        raise HTTPException(500, f"Failed to fetch PR diff: {str(e)}")
    except Exception as e:
        logger.error(f"[Webhook {delivery_id}] Unexpected error during review: {e}", exc_info=True)
        raise HTTPException(500, f"Unexpected error during review: {str(e)}")
