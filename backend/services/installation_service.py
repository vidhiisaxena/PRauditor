"""Installation persistence: read from and upsert into our own database."""

from typing import List, Optional

from sqlalchemy.orm import Session

from backend import models


def get_user_installations(db: Session, user_id: int) -> List[models.Installation]:
    return (
        db.query(models.Installation)
        .filter(models.Installation.user_id == user_id)
        .order_by(models.Installation.id)
        .all()
    )


def get_by_github_id(
    db: Session, github_installation_id: int
) -> Optional[models.Installation]:
    return (
        db.query(models.Installation)
        .filter(models.Installation.github_installation_id == github_installation_id)
        .first()
    )


def upsert_installation(
    db: Session,
    *,
    github_installation_id: int,
    user_id: Optional[int],
    account_login: Optional[str],
    account_type: Optional[str],
    target_type: Optional[str],
) -> models.Installation:
    """Insert or update an installation, keyed by its GitHub installation id."""
    inst = get_by_github_id(db, github_installation_id)
    if inst:
        if user_id is not None:
            inst.user_id = user_id
        inst.account_login = account_login
        inst.account_type = account_type
        inst.target_type = target_type
    else:
        inst = models.Installation(
            github_installation_id=github_installation_id,
            user_id=user_id,
            account_login=account_login,
            account_type=account_type,
            target_type=target_type,
        )
        db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


def delete_installation(
    db: Session, *, user_id: int, github_installation_id: int
) -> bool:
    """Remove a user's installation and deactivate its repositories.

    Returns False if no matching installation is owned by this user.
    """
    inst = (
        db.query(models.Installation)
        .filter(
            models.Installation.github_installation_id == github_installation_id,
            models.Installation.user_id == user_id,
        )
        .first()
    )
    if inst is None:
        return False

    db.query(models.Repository).filter(
        models.Repository.installation_id == github_installation_id
    ).update({models.Repository.active: False})
    db.delete(inst)
    db.commit()
    return True
