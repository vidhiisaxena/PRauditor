from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from .. import models
from ..schema import RepositoryOut, PullRequestOut

router = APIRouter(prefix="/api/repos", tags=["repositories"])

@router.get("/repositories", response_model=list[RepositoryOut])
def list_repositories(db: Session = Depends(get_db)):
    return db.query(models.Repository).order_by(models.Repository.full_name).all()


@router.get("/{repo_id}/prs", response_model=list[PullRequestOut])
def list_pull_requests(repo_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.PullRequest)
        .filter(models.PullRequest.repo_id == repo_id)
        .order_by(models.PullRequest.pr_number.desc())
        .all()
    )

@router.get("/{repo_id}")
def get_repo(repo_id: int, db: Session = Depends(get_db)):
    """
    Returns basic information about a repository, including the number of PRs and the last review date.{
    "id": 1,
    "name": "PRAuditor",
    "prs": 32,
    "last_review": "...",
    "critical": 19
    }
    """
    repo= db.query(models.Repository).filter(models.Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(404, f"Repository with id {repo_id} not found")
    
    total_prs= db.query(models.PullRequest).filter(models.PullRequest.repo_id == repo.id).count()
    last_reviewed_at = (
        db.query(func.max(models.PullRequest.last_reviewed_at))
        .filter(models.PullRequest.repo_id == repo.id)
        .scalar()
    )
    critical_issues_count = (
        db.query(func.count(models.ReviewIssue.id))
        .join(models.PullRequest, models.ReviewIssue.pr_id == models.PullRequest.id)
        .filter(
            models.PullRequest.repo_id == repo.id,
            models.ReviewIssue.severity == "critical",
        )
        .scalar()
    )

    return {
        "id": repo.id,
        "name": repo.full_name,
        "prs": total_prs,
        "last_review": last_reviewed_at.isoformat() if last_reviewed_at else None,
        "critical": critical_issues_count,
    } 
    