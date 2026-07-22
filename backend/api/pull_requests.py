from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend import models
from backend.schemas import ReviewIssueOut
from backend.integrations.github.client import fetch_pr_diff
from backend.services.review_service import run_and_store_review

router = APIRouter(prefix="/api/prs", tags=["pull_requests"])


@router.get("/{pr_id}/issues", response_model=list[ReviewIssueOut])
def list_review_issues(pr_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.ReviewIssue)
        .filter(models.ReviewIssue.pr_id == pr_id)
        .order_by(models.ReviewIssue.created_at.desc())
        .all()
    )


@router.get("/{pr_id}/summary")
def get_pr_summary(pr_id: int, db: Session = Depends(get_db)):
    """Summary of a PR, including issue counts by severity."""
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
    """Returns the unified diff for a PR (fetched live from GitHub)."""
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


# ---------------------------- POST endpoints -------------------------------


@router.post("/{id}/rerun")
def rerun_review(id: int, db: Session = Depends(get_db)):
    """Re-run the review for a specific PR by id."""
    pr = db.query(models.PullRequest).filter(models.PullRequest.id == id).first()
    if not pr:
        raise HTTPException(404, f"Pull request with id {id} not found")

    repo = db.query(models.Repository).filter(models.Repository.id == pr.repo_id).first()
    if not repo:
        raise HTTPException(404, f"Repository for PR id {id} not found")

    try:
        issues = run_and_store_review(db, repo, pr, repo.installation_id)
    except ValueError as e:
        raise HTTPException(500, f"Failed to fetch PR diff: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Unexpected error during review: {str(e)}")

    return JSONResponse({"reviewed": True, "issues": len(issues)})
