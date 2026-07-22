from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from backend.core.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, unique=True, index=True)  # owner/repo
    installation_id = Column(Integer, nullable=True)  # GitHub App installation that owns this repo

    pull_requests = relationship("PullRequest", back_populates="repository")
