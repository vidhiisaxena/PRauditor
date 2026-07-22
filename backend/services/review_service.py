from typing import List

from sqlalchemy.orm import Session

from backend import models
from backend.review.types import Issue
from backend.review.pipeline import run_review
from backend.review.markdown import issues_to_markdown
from backend.integrations.github.client import fetch_pr_diff, post_pr_comment


def run_and_store_review(
    db: Session,
    repo: "models.Repository",
    pr: "models.PullRequest",
    installation_id: int,
) -> List[Issue]:
    """
    Fetch the PR diff, run the review pipeline, replace the PR's stored issues,
    and post the review comment back to GitHub. Returns the issues.

    Shared by the webhook (automatic) and the rerun endpoint (manual) so the
    review flow lives in exactly one place.
    """
    diff = fetch_pr_diff(repo.full_name, pr.pr_number, installation_id)

    issues = run_review(diff)

    # Replace the PR's issues with the new set.
    db.query(models.ReviewIssue).filter(models.ReviewIssue.pr_id == pr.id).delete()
    for issue in issues:
        db.add(
            models.ReviewIssue(
                pr_id=pr.id,
                file_path=issue.file_path,
                line=issue.line,
                kind=issue.kind,
                severity=issue.severity,
                message=issue.message,
                suggestion=issue.suggestion,
            )
        )
    db.commit()

    # Posting the comment is best-effort; the review is already saved.
    try:
        post_pr_comment(
            repo.full_name, pr.pr_number, issues_to_markdown(issues), installation_id
        )
    except Exception as e:  # noqa: BLE001
        print(f"Warning: Failed to post PR comment: {e}")

    return issues
