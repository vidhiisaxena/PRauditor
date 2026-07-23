#Create/update users from a GitHub profile, and look them up.

from typing import Optional

from sqlalchemy.orm import Session

from backend import models


def upsert_user_from_github(
    db: Session, profile: dict, email: Optional[str]
) -> models.User:
    """Insert or update the user identified by their GitHub id."""
    github_id = profile["id"]
    user = db.query(models.User).filter(models.User.github_id == github_id).first()

    if user:
        user.username = profile.get("login")
        user.name = profile.get("name")
        user.email = email or user.email
        user.avatar_url = profile.get("avatar_url")
    else:
        user = models.User(
            github_id=github_id,
            username=profile.get("login"),
            name=profile.get("name"),
            email=email,
            avatar_url=profile.get("avatar_url"),
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()
