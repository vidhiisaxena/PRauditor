import json
from fastapi import APIRouter, FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from backend.markdown import issues_to_markdown 
from backend.review_pipeline import run_review 

from ..database import get_db
from .. import models
from ..config import GITHUB_INSTALLATION_ID

from ..github_webhook_utils import check_signature
from ..github_client import (
    fetch_pr_diff,
    post_pr_comment,
)

router=APIRouter(prefix="/api/prs", tags=["pull_requests"])

@router.get("/{pr_id}/issues", response_model=list[models.ReviewIssue])
def list_review_issues(pr_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.ReviewIssue)
        .filter(models.ReviewIssue.pr_id == pr_id)
        .order_by(models.ReviewIssue.created_at.desc())
        .all()
    )

@router.get("/{pr_id}/summary")
def get_pr_summary(pr_id: int, db: Session = Depends(get_db)):
    """
    Returns a summary of a PR, including the number of issues by severity.
    {
        "id": 1,
        "repo": "owner/repo",
        "pr_number": 42,
        "title": "Fix bug in feature X",
        "state": "open",
        "head_sha": "...",
        "last_reviewed_at": "...",
        "issues": {
            "critical": 2,
            "major": 5,
            "minor": 10
        }
    }
    """
    pr = db.query(models.PullRequest).filter(models.PullRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(404, f"Pull request with id {pr_id} not found")

    repo = db.query(models.Repository).filter(models.Repository.id == pr.repo_id).first()
    if not repo:
        raise HTTPException(404, f"Repository for PR id {pr_id} not found")

    severity_counts = (
        db.query(models.ReviewIssue.severity, func.count(models.ReviewIssue.id))
        .filter(models.ReviewIssue.pr_id == pr.id)
        .group_by(models.ReviewIssue.severity)
        .all()
    )
    severity_dict = {severity: count for severity, count in severity_counts}

    return {
        "id": pr.id,
        "repo": repo.full_name,
        "pr_number": pr.pr_number,
        "title": pr.title,
        "state": pr.state,
        "head_sha": pr.head_sha,
        "last_reviewed_at": pr.last_reviewed_at.isoformat() if pr.last_reviewed_at else None,
        "issues": {
            "critical": severity_dict.get("critical", 0),
            "major": severity_dict.get("major", 0),
            "minor": severity_dict.get("minor", 0),
            "info": severity_dict.get("info", 0),
        },
    }
    
    
@router.get("/{pr_id}/diff")
def get_pr_diff(pr_id: int, db: Session = Depends(get_db)):
    """
    Returns the unified diff for a PR.
    """
    pr = db.query(models.PullRequest).filter(models.PullRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(404, f"Pull request with id {pr_id} not found")

    repo = db.query(models.Repository).filter(models.Repository.id == pr.repo_id).first()
    if not repo:
        raise HTTPException(404, f"Repository for PR id {pr_id} not found")

    try:
        diff = fetch_pr_diff(repo.full_name, pr.pr_number, repo.installation_id)
    except ValueError as e:
        raise HTTPException(500, f"Failed to fetch PR diff: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Unexpected error fetching PR diff: {str(e)}")

    return JSONResponse({"diff": diff})

# ---------------------------- POST API ENDPOINTS --------------------------------------------

@router.post("/{id}/rerun")
def rerun_review(id: int, db: Session = Depends(get_db)):
    """
    Rerun the review for a specific PR by ID.
    """
    pr = db.query(models.PullRequest).filter(models.PullRequest.id == id).first()
    if not pr:
        raise HTTPException(404, f"Pull request with id {id} not found")

    repo = db.query(models.Repository).filter(models.Repository.id == pr.repo_id).first()
    if not repo:
        raise HTTPException(404, f"Repository for PR id {id} not found")

    try:
        diff = fetch_pr_diff(repo.full_name, pr.pr_number, repo.installation_id)
    except ValueError as e:
        raise HTTPException(500, f"Failed to fetch PR diff: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Unexpected error fetching PR diff: {str(e)}")

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
        post_pr_comment(repo.full_name, pr.pr_number, markdown_comment, repo.installation_id)
    except ValueError as e:
        # Log but don't fail the rerun - review was completed
        print(f"Warning: Failed to post PR comment: {str(e)}")
    except Exception as e:
        print(f"Warning: Unexpected error posting PR comment: {str(e)}")

    return JSONResponse({"reviewed": True, "issues": len(issues)})



    