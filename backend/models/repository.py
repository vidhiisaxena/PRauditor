from sqlalchemy import Boolean, Column, Integer, String, text
from sqlalchemy.orm import relationship

from backend.core.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, unique=True, index=True)  # owner/repo
    installation_id = Column(Integer, nullable=True)  # GitHub App installation that owns this repo

    # --- added for self-serve onboarding / repo sync ---
    github_id = Column(Integer, nullable=True, index=True)  # GitHub's repo id
    private = Column(Boolean, nullable=True, default=False)
    # active = still accessible via the installation. Repos removed from an
    # installation are deactivated (not deleted) by the sync so history is kept.
    active = Column(Boolean, nullable=False, default=True, server_default=text("true"))

    pull_requests = relationship("PullRequest", back_populates="repository")
