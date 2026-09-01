"""Repository business logic: sync an installation's repos and list them."""

from typing import List

from sqlalchemy.orm import Session

from backend import models
from backend.integrations.github.client import fetch_repository_prs
from backend.services import github_app


def sync_repository_prs(repo_id: int, repo_full_name: str, repo_installation_id: int) -> List[models.PullRequest]:
    """Upsert the PRs currently visible on GitHub for a repository into our DB."""
    if repo_installation_id is None:
        return []

    try:
        github_prs = fetch_repository_prs(repo_full_name, repo_installation_id)
    except Exception:
        with SessionLocal() as db:
            return (
                db.query(models.PullRequest)
                .filter(models.PullRequest.repo_id == repo_id)
                .order_by(models.PullRequest.pr_number.desc())
                .all()
            )

    fetched_numbers: set[int] = set()
    with SessionLocal() as db:
        try:
            for gh_pr in github_prs:
                pr_number = gh_pr.get("number")
                if pr_number is None:
                    continue
                fetched_numbers.add(pr_number)

                state = gh_pr.get("state")
                if gh_pr.get("merged_at") is not None and state == "closed":
                    state = "merged"

                pr = (
                    db.query(models.PullRequest)
                    .filter(
                        models.PullRequest.repo_id == repo_id,
                        models.PullRequest.pr_number == pr_number,
                    )
                    .first()
                )
                if pr is None:
                    pr = models.PullRequest(
                        repo_id=repo_id,
                        pr_number=pr_number,
                        title=gh_pr.get("title"),
                        state=state,
                        head_sha=(gh_pr.get("head") or {}).get("sha"),
                    )
                    db.add(pr)
                else:
                    pr.title = gh_pr.get("title")
                    pr.state = state
                    pr.head_sha = (gh_pr.get("head") or {}).get("sha")

            # Keep historical rows for PRs no longer visible on GitHub but do not create
            # duplicate records for newly discovered ones.
            for pr in (
                db.query(models.PullRequest)
                .filter(models.PullRequest.repo_id == repo_id)
                .all()
            ):
                if pr.pr_number not in fetched_numbers and pr.pr_number is not None:
                    pr.state = "closed" if pr.state != "merged" else "merged"

            db.commit()

            return (
                db.query(models.PullRequest)
                .filter(models.PullRequest.repo_id == repo_id)
                .order_by(models.PullRequest.pr_number.desc())
                .all()
            )
        except Exception:
            db.rollback()
            raise


from backend.core.database import SessionLocal

def sync_installation_repositories(
    github_installation_id: int
) -> List[models.Repository]:
    """
    Sync the repositories accessible to one installation into our database.

    Idempotent: upserts by unique `full_name` (no duplicates on re-run).
    Transactional: a single commit at the end; any failure rolls back.
    Deactivates repos previously under this installation that are no longer
    accessible (they are kept, not deleted, so review history survives).
    """
    gh_repos = github_app.list_installation_repositories(github_installation_id)

    fetched_full_names: set[str] = set()
    with SessionLocal() as db:
        try:
            for gh in gh_repos:
                full_name = gh.get("full_name")
                if not full_name:
                    continue
                fetched_full_names.add(full_name)

                repo = (
                    db.query(models.Repository)
                    .filter(models.Repository.full_name == full_name)
                    .first()
                )
                if repo is None:
                    repo = models.Repository(full_name=full_name)
                    db.add(repo)

                repo.github_id = gh.get("id")
                repo.private = bool(gh.get("private", False))
                repo.installation_id = github_installation_id
                repo.active = True

            # Deactivate repos previously synced under this installation that are
            # no longer returned by GitHub.
            previously_synced = (
                db.query(models.Repository)
                .filter(models.Repository.installation_id == github_installation_id)
                .all()
            )
            for repo in previously_synced:
                if repo.full_name not in fetched_full_names:
                    repo.active = False

            db.commit()
            
            return get_installation_repositories(db, github_installation_id)
        except Exception:
            db.rollback()
            raise


def get_installation_repositories(
    db: Session, github_installation_id: int
) -> List[models.Repository]:
    return (
        db.query(models.Repository)
        .filter(
            models.Repository.installation_id == github_installation_id,
            models.Repository.active.is_(True),
        )
        .order_by(models.Repository.full_name)
        .all()
    )


def get_user_repositories(db: Session, user_id: int) -> List[models.Repository]:
    """Active repositories across every installation owned by the user."""
    installation_ids = [
        i.github_installation_id
        for i in db.query(models.Installation)
        .filter(models.Installation.user_id == user_id)
        .all()
    ]
    if not installation_ids:
        return []
    return (
        db.query(models.Repository)
        .filter(
            models.Repository.installation_id.in_(installation_ids),
            models.Repository.active.is_(True),
        )
        .order_by(models.Repository.full_name)
        .all()
    )
