"""Repository business logic: sync an installation's repos and list them."""

from typing import List

from sqlalchemy.orm import Session

from backend import models
from backend.services import github_app


def sync_installation_repositories(
    db: Session, installation: "models.Installation"
) -> List[models.Repository]:
    """
    Sync the repositories accessible to one installation into our database.

    Idempotent: upserts by unique `full_name` (no duplicates on re-run).
    Transactional: a single commit at the end; any failure rolls back.
    Deactivates repos previously under this installation that are no longer
    accessible (they are kept, not deleted, so review history survives).
    """
    github_installation_id = installation.github_installation_id
    gh_repos = github_app.list_installation_repositories(github_installation_id)

    fetched_full_names: set[str] = set()
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
    except Exception:
        db.rollback()
        raise

    return get_installation_repositories(db, github_installation_id)


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
