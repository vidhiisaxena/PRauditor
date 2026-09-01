import json
import logging

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.database import SessionLocal
from backend import models
from backend.integrations.github.webhook_utils import check_signature
from backend.services import installation_service, repository_service, job_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["webhook"])


@router.post("/github/webhook")
async def webhook(request: Request):
    delivery_id = request.headers.get("X-GitHub-Delivery", "unknown")
    logger.info(f"[Webhook {delivery_id}] Received GitHub webhook")
    
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    content_type = request.headers.get("content-type", "")

    # Parse payload
    try:
        if content_type.startswith("application/x-www-form-urlencoded"):
            form = await request.form()
            payload = form.get("payload")
            if not payload:
                logger.error(f"[Webhook {delivery_id}] Missing payload in form data")
                raise HTTPException(400, "Missing payload")
            data = json.loads(payload)
        else:
            data = json.loads(raw_body.decode())
    except json.JSONDecodeError as e:
        logger.error(f"[Webhook {delivery_id}] Failed to parse JSON: {e}")
        raise HTTPException(400, "Invalid JSON body")

    event = request.headers.get("X-GitHub-Event")
    action = data.get("action")
    logger.info(f"[Webhook {delivery_id}] GitHub event: {event}, action: {action}")

    # Verify signature
    if not check_signature(signature, raw_body):
        logger.error(f"[Webhook {delivery_id}] Signature verification failed")
        raise HTTPException(401, "Invalid signature")

    # Handle ping
    if event == "ping":
        logger.info(f"[Webhook {delivery_id}] Ping event, responding OK")
        return {"ok": True}

    # Handle installation lifecycle events
    if event == "installation":
        return await handle_installation_event(delivery_id, data, action)

    # Handle pull request events
    if event == "pull_request":
        return await handle_pull_request_event(delivery_id, data, action)

    logger.info(f"[Webhook {delivery_id}] Ignoring event type: {event}")
    return {"ignored": True}


async def handle_installation_event(delivery_id: str, data: dict, action: str):
    """
    Handle GitHub App installation lifecycle events:
    - installation.created
    - installation.deleted
    """
    if action not in ("created", "deleted"):
        logger.info(f"[Webhook {delivery_id}] Ignoring installation action: {action}")
        return {"ignored": True}

    installation = data.get("installation", {})
    github_installation_id = installation.get("id")
    if not github_installation_id:
        logger.error(f"[Webhook {delivery_id}] Missing installation ID in installation event")
        raise HTTPException(400, "Missing installation ID")

    account = installation.get("account", {})
    account_login = account.get("login")
    account_type = account.get("type")
    target_type = installation.get("target_type")

    logger.info(
        f"[Webhook {delivery_id}] Installation {action} event: "
        f"github_installation_id={github_installation_id}, "
        f"account_login={account_login}, account_type={account_type}"
    )

    if action == "created":
        with SessionLocal() as db:
            try:
                inst = installation_service.upsert_installation(
                    db,
                    github_installation_id=github_installation_id,
                    user_id=None,  # We don't have user info from the webhook
                    account_login=account_login,
                    account_type=account_type,
                    target_type=target_type,
                )
                logger.info(f"[Webhook {delivery_id}] Installation persisted: {github_installation_id}")
                
                # Sync repositories for this installation
                try:
                    synced_repos = repository_service.sync_installation_repositories(inst.github_installation_id)
                    logger.info(
                        f"[Webhook {delivery_id}] Installation {github_installation_id} synced "
                        f"{len(synced_repos)} repositories"
                    )
                except Exception as e:
                    logger.error(
                        f"[Webhook {delivery_id}] Failed to sync repositories for installation "
                        f"{github_installation_id}: {e}"
                    )
            except Exception as e:
                db.rollback()
                logger.error(
                    f"[Webhook {delivery_id}] Failed to persist installation {github_installation_id}: {e}"
                )
                raise HTTPException(500, f"Failed to persist installation: {str(e)}")

    elif action == "deleted":
        with SessionLocal() as db:
            try:
                inst = installation_service.get_by_github_id(db, github_installation_id)
                if inst:
                    installation_service.delete_installation(
                        db, user_id=inst.user_id, github_installation_id=github_installation_id
                    )
                    logger.info(f"[Webhook {delivery_id}] Installation deleted: {github_installation_id}")
                else:
                    logger.warning(
                        f"[Webhook {delivery_id}] Installation {github_installation_id} not found in DB"
                    )
            except Exception as e:
                db.rollback()
                logger.error(
                    f"[Webhook {delivery_id}] Failed to delete installation {github_installation_id}: {e}"
                )
                raise HTTPException(500, f"Failed to delete installation: {str(e)}")

    return {"acknowledged": True}


async def handle_pull_request_event(delivery_id: str, data: dict, action: str):
    """
    Handle GitHub pull_request webhook events.
    
    Architectural flow:
    1. Extract installation.id from payload directly
    2. Extract GitHub repository ID
    3. Look up Repository and upsert PullRequest
    4. Create ReviewJob using (installation_id, pr_id, head_sha)
    5. Return 202 Accepted
    """
    if action not in ("opened", "reopened", "synchronize"):
        logger.info(f"[Webhook {delivery_id}] Ignoring pull_request action: {action}")
        return {"ignored": True}

    # Extract installation_id explicitly
    installation_id = data.get("installation", {}).get("id")
    if not installation_id:
        logger.error(f"[Webhook {delivery_id}] Missing installation.id in PR event")
        raise HTTPException(400, "Missing installation ID in payload")

    # Extract core identifiers from payload
    repository_data = data.get("repository", {})
    github_repo_id = repository_data.get("id")
    repo_full_name = repository_data.get("full_name")

    if not github_repo_id or not repo_full_name:
        logger.error(f"[Webhook {delivery_id}] Missing GitHub repository information")
        raise HTTPException(400, "Missing repository information")

    pr_data = data.get("pull_request", {})
    pr_number = pr_data.get("number")
    pr_title = pr_data.get("title")
    pr_state = pr_data.get("state")
    pr_head_sha = pr_data.get("head", {}).get("sha")

    if not pr_number or not pr_head_sha:
        logger.error(f"[Webhook {delivery_id}] Missing PR number or head SHA")
        raise HTTPException(400, "Missing PR details")

    try:
        with SessionLocal() as db:
            repo = db.query(models.Repository).filter(
                models.Repository.github_id == github_repo_id
            ).first()

            if not repo:
                logger.warning(
                    f"[Webhook {delivery_id}] Repository not found: github_repo_id={github_repo_id}, "
                    f"full_name={repo_full_name}. Repository must be synced first."
                )
                db.rollback()
                return JSONResponse(
                    {
                        "status": "ignored",
                        "reason": "repository_not_registered",
                        "message": f"Repository {repo_full_name} is not registered."
                    },
                    status_code=202
                )

            # Update repository metadata if needed
            repo.full_name = repo_full_name
            if repo.github_id is None:
                repo.github_id = github_repo_id
            repo.active = True  # Ensure it's marked active

            # Upsert pull request
            pr = db.query(models.PullRequest).filter(
                models.PullRequest.repo_id == repo.id,
                models.PullRequest.pr_number == pr_number,
            ).first()

            if not pr:
                pr = models.PullRequest(
                    repo_id=repo.id,
                    pr_number=pr_number,
                    title=pr_title,
                    state=pr_state,
                    head_sha=pr_head_sha,
                )
                db.add(pr)
            else:
                pr.title = pr_title
                pr.state = pr_state
                pr.head_sha = pr_head_sha

            db.flush() # Flush to get pr.id but do not commit yet
            
            pr_id = pr.id
            repo_id = repo.id

            # Create the job within the same transaction.
            job = job_service.create_review_job(pr_id, installation_id, pr_head_sha, db=db)
            db.commit() # commit the full transaction (Repo + PR + Job)
        
        if not job:
            logger.error(f"[Webhook {delivery_id}] Failed to create or retrieve ReviewJob")
            raise HTTPException(500, "Failed to create review job")
            
        # Logging
        # Determine if it's a new or duplicate by checking the status
        # Since create_review_job handles ON CONFLICT, if it returns an existing job we just use it
        # Unfortunately, create_review_job does not currently return a flag "created: bool".
        # But we can assume if it exists, we successfully enqueued or it's already there.
        
        logger.info(
            f"[Webhook {delivery_id}] PR event processed: event=pull_request action={action} "
            f"repo={repo_full_name} pr={pr_number} installation={installation_id} "
            f"head_sha={pr_head_sha} job_id={job['id']} status={job['status']}"
        )
        
        # We always return 202 whether it's duplicate or not
        return JSONResponse(
            {
                "ok": True,
                "queued": True,
                "job_id": job["id"]
            },
            status_code=202
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[Webhook {delivery_id}] Database transaction failed: {e}",
            exc_info=True
        )
        raise HTTPException(500, "Internal server error during database operation")
