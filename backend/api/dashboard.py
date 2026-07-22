from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.api.deps import get_db
from backend import models

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    """Returns basic statistics for the dashboard."""
    total_repos = db.query(models.Repository).count()
    total_prs = db.query(models.PullRequest).count()
    total_issues = db.query(models.ReviewIssue).count()

    severity_counts = (
        db.query(models.ReviewIssue.severity, func.count(models.ReviewIssue.id))
        .group_by(models.ReviewIssue.severity)
        .all()
    )
    severity_dict = {severity: count for severity, count in severity_counts}

    return {
        "repositories": total_repos,
        "pull_requests": total_prs,
        "reviews": total_issues,
        "critical": severity_dict.get("critical", 0),
        "major": severity_dict.get("major", 0),
        "minor": severity_dict.get("minor", 0),
    }
