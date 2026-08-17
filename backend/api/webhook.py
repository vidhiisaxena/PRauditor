import json
import logging

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend import models
from backend.integrations.github.webhook_utils import check_signature
from backend.services.review_service import run_and_store_review
from backend.services import installation_service, repository_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["webhook"])


@router.post("/github/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
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
        return await handle_installation_event(db, delivery_id, data, action)

    # Handle pull request events
    if event == "pull_request":
        return await handle_pull_request_event(db, delivery_id, data, action)

    logger.info(f"[Webhook {delivery_id}] Ignoring event type: {event}")
    return {"ignored": True}


async def handle_installation_event(db: Session, delivery_id: str, data: dict, action: str):
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
                synced_repos = repository_service.sync_installation_repositories(db, inst)
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
            logger.error(
                f"[Webhook {delivery_id}] Failed to persist installation {github_installation_id}: {e}"
            )
            raise HTTPException(500, f"Failed to persist installation: {str(e)}")

    elif action == "deleted":
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
            logger.error(
                f"[Webhook {delivery_id}] Failed to delete installation {github_installation_id}: {e}"
            )
            raise HTTPException(500, f"Failed to delete installation: {str(e)}")

    return {"acknowledged": True}


async def handle_pull_request_event(db: Session, delivery_id: str, data: dict, action: str):
    """
    Handle GitHub pull_request webhook events.
    
    Architectural flow:
    1. Extract GitHub repository ID (immutable, rename-safe identifier)
    2. Look up Repository by github_id
    3. Resolve installation_id from repository.installation_id
    4. Upsert PR and run audit pipeline
    """
    if action not in ("opened", "reopened", "synchronize"):
        logger.info(f"[Webhook {delivery_id}] Ignoring pull_request action: {action}")
        return {"ignored": True}

    # Extract core identifiers from payload
    repository_data = data.get("repository", {})
    github_repo_id = repository_data.get("id")
    repo_full_name = repository_data.get("full_name")

    if not github_repo_id:
        logger.error(f"[Webhook {delivery_id}] Missing GitHub repository ID")
        raise HTTPException(400, "Missing repository ID")

    if not repo_full_name:
        logger.error(f"[Webhook {delivery_id}] Missing repository full_name")
        raise HTTPException(400, "Missing repository full_name")

    pr_data = data.get("pull_request", {})
    pr_number = pr_data.get("number")

    if not pr_number:
        logger.error(f"[Webhook {delivery_id}] Missing PR number")
        raise HTTPException(400, "Missing PR number")

    logger.info(
        f"[Webhook {delivery_id}] Pull request event: {repo_full_name}#{pr_number}, "
        f"action={action}, github_repo_id={github_repo_id}"
    )

    # CRITICAL: Look up the repository to get its installation_id
    # This is the architectural anchor: repositories must exist in our DB before we audit them
    repo = db.query(models.Repository).filter(
        models.Repository.github_id == github_repo_id
    ).first()

    if not repo:
        logger.warning(
            f"[Webhook {delivery_id}] Repository not found in database: "
            f"github_repo_id={github_repo_id}, full_name={repo_full_name}. "
            f"The repository must be synced through a GitHub App installation before PRs can be audited."
        )
        # Return 202 Accepted to avoid GitHub retries, but don't audit
        # The user should install the app or sync the repository
        return JSONResponse(
            {
                "status": "ignored",
                "reason": "repository_not_registered",
                "message": f"Repository {repo_full_name} is not registered with PRAuditor. "
                "Please ensure the GitHub App is installed on this repository."
            },
            status_code=202
        )

    installation_id = repo.installation_id
    if not installation_id:
        logger.error(
            f"[Webhook {delivery_id}] Repository {repo_full_name} exists but has no installation_id. "
            f"This is a database consistency error."
        )
        raise HTTPException(
            500,
            "Repository exists but installation_id is missing (database consistency error)"
        )

    logger.info(
        f"[Webhook {delivery_id}] Resolved installation_id={installation_id} for repository "
        f"{repo_full_name} (github_repo_id={github_repo_id})"
    )

    # Update repository metadata if needed
    repo.full_name = repo_full_name
    if repo.github_id is None:
        repo.github_id = github_repo_id
    repo.active = True  # Ensure it's marked active
    db.commit()

    # Upsert pull request
    pr = db.query(models.PullRequest).filter(
        models.PullRequest.repo_id == repo.id,
        models.PullRequest.pr_number == pr_number,
    ).first()

    pr_title = pr_data.get("title")
    pr_state = pr_data.get("state")
    pr_head_sha = pr_data.get("head", {}).get("sha")

    if not pr:
        logger.info(f"[Webhook {delivery_id}] Creating PR record: {repo_full_name}#{pr_number}")
        pr = models.PullRequest(
            repo_id=repo.id,
            pr_number=pr_number,
            title=pr_title,
            state=pr_state,
            head_sha=pr_head_sha,
        )
        db.add(pr)
    else:
        logger.debug(f"[Webhook {delivery_id}] Updating PR record: {repo_full_name}#{pr_number}")
        pr.title = pr_title
        pr.state = pr_state
        pr.head_sha = pr_head_sha

    db.commit()
    db.refresh(pr)

    # Run the audit pipeline
    try:
        logger.info(
            f"[Webhook {delivery_id}] Starting audit pipeline: {repo_full_name}#{pr_number} "
            f"(repo_id={repo.id}, pr_id={pr.id}, installation_id={installation_id})"
        )
        issues = run_and_store_review(db, repo, pr, installation_id)
        logger.info(
            f"[Webhook {delivery_id}] Audit completed: {repo_full_name}#{pr_number} "
            f"found {len(issues)} issues"
        )
        return JSONResponse({"reviewed": True, "issues_found": len(issues)})
    except ValueError as e:
        logger.error(
            f"[Webhook {delivery_id}] Audit pipeline failed (ValueError): {e}",
            exc_info=True
        )
        raise HTTPException(500, f"Audit pipeline failed: {str(e)}")
    except Exception as e:
        logger.error(
            f"[Webhook {delivery_id}] Audit pipeline failed (Exception): {e}",
            exc_info=True
        )
        raise HTTPException(500, f"Audit pipeline failed: {str(e)}")
