from typing import List

from backend.core.database import SessionLocal
from backend import models
from backend.review.types import Issue
from backend.review.pipeline import run_review
from backend.review.markdown import issues_to_markdown
from backend.integrations.github.client import fetch_pr_diff, post_pr_comment


def run_and_store_review(
    repo_full_name: str,
    pr_number: int,
    pr_id: int,
    installation_id: int,
    job_head_sha: str = None,
    pr_title: str = "",
) -> List[Issue]:
    """
    Fetch the PR diff, run the review pipeline, replace the PR's stored issues,
    and post the review comment back to GitHub. Returns the issues.
    
    If `job_head_sha` is provided, verifies that the PR's current head_sha
    still matches before persisting, ensuring stale reviews do not overwrite
    newer reviews.
    """
    # NO DB SESSION
    diff = fetch_pr_diff(repo_full_name, pr_number, installation_id)

    issues = run_review(diff, pr_title=pr_title)

    # DB SESSION
    with SessionLocal() as db:
        try:
            pr = db.query(models.PullRequest).filter(models.PullRequest.id == pr_id).with_for_update().first()
            if not pr:
                print(f"Warning: PR {pr_id} not found in DB.")
                return []
                
            if job_head_sha and pr.head_sha != job_head_sha:
                print(f"Stale review safely skipped: Job SHA={job_head_sha}, Current PR SHA={pr.head_sha}")
                # DO NOT persist findings, do not delete existing findings
                return []
                
            # Replace the PR's issues with the new set.
            db.query(models.ReviewIssue).filter(models.ReviewIssue.pr_id == pr_id).delete()
            for issue in issues:
                db.add(
                    models.ReviewIssue(
                        pr_id=pr_id,
                        file_path=issue.file_path,
                        line=issue.line,
                        kind=issue.kind,
                        severity=issue.severity,
                        message=issue.message,
                        suggestion=issue.suggestion,
                    )
                )
            db.commit()
        except Exception:
            db.rollback()
            raise

    # NO DB SESSION
    # Posting the comment is best-effort; the review is already saved.
    try:
        post_pr_comment(
            repo_full_name, pr_number, issues_to_markdown(issues), installation_id
        )
    except Exception as e:  # noqa: BLE001
        print(f"Warning: Failed to post PR comment: {e}")

    return issues
