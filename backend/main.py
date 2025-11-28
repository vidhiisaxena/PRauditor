import json
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend import models
from backend.config import GITHUB_INSTALLATION_ID

from backend.github_webhook_utils import check_signature
from backend.github_client import (
    fetch_pr_diff,
    post_pr_comment,
)

from backend.review_pipeline import run_review
from backend.markdown import issues_to_markdown

from backend.schema import RepositoryOut, PullRequestOut, ReviewIssueOut


app = FastAPI()


@app.get("/")
def home():
    return {"status": "ok"}


@app.post("/github/webhook")
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
        except:
            raise HTTPException(400, "Invalid JSON inside form payload")
    else:
        try:
            data = json.loads(raw_body.decode())
        except:
            raise HTTPException(400, "Invalid JSON body")

    event = request.headers.get("X-GitHub-Event")
    action = data.get("action")

    # 2. Signature verification
    if not check_signature(signature, raw_body):
        raise HTTPException(401, "Invalid signature")

    # Ping event
    if event == "ping":
        return {"ok": True}

    # Accept PR events only
    if event != "pull_request":
        return {"ignored": True}

    if action not in ("opened", "reopened", "synchronize"):
        return {"ignored": True}

    # Extract installation ID safely
    # Try from webhook payload first, fallback to config
    installation = data.get("installation")
    if installation and isinstance(installation, dict):
        installation_id = installation.get("id")
    else:
        installation_id = None
    
    # Fallback to config if not in payload
    if not installation_id and GITHUB_INSTALLATION_ID:
        try:
            installation_id = int(GITHUB_INSTALLATION_ID)
        except (ValueError, TypeError):
            installation_id = None
    
    if not installation_id:
        raise HTTPException(400, "Missing installation ID. Not found in webhook payload and GITHUB_INSTALLATION_ID not configured")
    
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

    # Upsert repository
    repo = db.query(models.Repository).filter(models.Repository.full_name == repo_full).first()
    if not repo:
        repo = models.Repository(full_name=repo_full)
        db.add(repo)
        db.commit()
        db.refresh(repo)

    # Upsert PR
    pr = (
        db.query(models.PullRequest)
        .filter(models.PullRequest.repo_id == repo.id, models.PullRequest.pr_number == pr_number)
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

    # Fetch diff
    try:
        diff = fetch_pr_diff(repo_full, pr_number, installation_id)
    except ValueError as e:
        raise HTTPException(500, f"Failed to fetch PR diff: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Unexpected error fetching PR diff: {str(e)}")

    # Run AI review
    issues = run_review(diff)

    # Replace issues in DB
    db.query(models.ReviewIssue).filter(models.ReviewIssue.pr_id == pr.id).delete()
    for issue in issues:
        row = models.ReviewIssue(
            pr_id=pr.id,
            file_path=issue.file_path,
            line=issue.line,
            kind=issue.kind,
            severity=issue.severity,
            message=issue.message,
            suggestion=issue.suggestion,
        )
        db.add(row)
    db.commit()

    # Post review comment
    try:
        markdown_comment = issues_to_markdown(issues)
        post_pr_comment(repo_full, pr_number, markdown_comment, installation_id)
    except ValueError as e:
        # Log but don't fail the webhook - review was completed
        print(f"Warning: Failed to post PR comment: {str(e)}")
    except Exception as e:
        print(f"Warning: Unexpected error posting PR comment: {str(e)}")

    return JSONResponse({"reviewed": True, "issues": len(issues)})


# ============================================================
#              📦 BASIC READ-ONLY API
# ============================================================

@app.get("/api/repos", response_model=list[RepositoryOut])
def list_repositories(db: Session = Depends(get_db)):
    return db.query(models.Repository).order_by(models.Repository.full_name).all()


@app.get("/api/repos/{repo_id}/prs", response_model=list[PullRequestOut])
def list_pull_requests(repo_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.PullRequest)
        .filter(models.PullRequest.repo_id == repo_id)
        .order_by(models.PullRequest.pr_number.desc())
        .all()
    )


@app.get("/api/prs/{pr_id}/issues", response_model=list[ReviewIssueOut])
def list_review_issues(pr_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.ReviewIssue)
        .filter(models.ReviewIssue.pr_id == pr_id)
        .order_by(models.ReviewIssue.created_at.desc())
        .all()
    )
