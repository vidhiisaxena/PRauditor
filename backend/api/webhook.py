import json

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend import models
from backend.core.config import GITHUB_INSTALLATION_ID
from backend.integrations.github.webhook_utils import check_signature
from backend.services.review_service import run_and_store_review

router = APIRouter(prefix="/api/webhook", tags=["webhook"])


@router.post("/github/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    content_type = request.headers.get("content-type", "")

    # 1. Parse payload
    if content_type.startswith("application/x-www-form-urlencoded"):
        form = await request.form()
        payload = form.get("payload")
        if not payload:
            raise HTTPException(400, "Missing payload")
        try:
            data = json.loads(payload)
        except Exception:
            raise HTTPException(400, "Invalid JSON inside form payload")
    else:
        try:
            data = json.loads(raw_body.decode())
        except Exception:
            raise HTTPException(400, "Invalid JSON body")

    event = request.headers.get("X-GitHub-Event")
    action = data.get("action")

    # 2. Verify signature
    if not check_signature(signature, raw_body):
        raise HTTPException(401, "Invalid signature")

    if event == "ping":
        return {"ok": True}

    if event != "pull_request":
        return {"ignored": True}

    if action not in ("opened", "reopened", "synchronize"):
        return {"ignored": True}

    # Installation id: prefer the webhook payload, fall back to config.
    installation = data.get("installation")
    installation_id = installation.get("id") if isinstance(installation, dict) else None
    if not installation_id and GITHUB_INSTALLATION_ID:
        try:
            installation_id = int(GITHUB_INSTALLATION_ID)
        except (ValueError, TypeError):
            installation_id = None
    if not installation_id:
        raise HTTPException(
            400,
            "Missing installation ID. Not found in webhook payload and "
            "GITHUB_INSTALLATION_ID not configured.",
        )

    repo_full = data.get("repository", {}).get("full_name")
    if not repo_full:
        raise HTTPException(400, "Missing repository data in webhook payload")

    pr_info = data.get("pull_request")
    if not pr_info:
        raise HTTPException(400, "Missing pull_request data in webhook payload")

    pr_number = pr_info.get("number")
    if not pr_number:
        raise HTTPException(400, "Missing PR number in webhook payload")

    title = pr_info.get("title")
    state = pr_info.get("state")
    head_sha = pr_info.get("head", {}).get("sha")

    # Upsert repository (and remember which installation owns it, so manual
    # reruns work later).
    repo = (
        db.query(models.Repository)
        .filter(models.Repository.full_name == repo_full)
        .first()
    )
    if not repo:
        repo = models.Repository(full_name=repo_full, installation_id=installation_id)
        db.add(repo)
        db.commit()
        db.refresh(repo)
    elif repo.installation_id != installation_id:
        repo.installation_id = installation_id
        db.commit()

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
        pr = models.PullRequest(
            repo_id=repo.id,
            pr_number=pr_number,
            title=title,
            state=state,
            head_sha=head_sha,
        )
        db.add(pr)
    else:
        pr.title = title
        pr.state = state
        pr.head_sha = head_sha
    db.commit()
    db.refresh(pr)

    # Fetch diff → review → store issues → post comment
    try:
        issues = run_and_store_review(db, repo, pr, installation_id)
    except ValueError as e:
        raise HTTPException(500, f"Failed to fetch PR diff: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Unexpected error during review: {str(e)}")

    return JSONResponse({"reviewed": True, "issues": len(issues)})
