from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from backend.core.database import Base


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"))
    pr_number = Column(Integer, index=True)
    title = Column(String)
    state = Column(String)  # open, closed, merged
    head_sha = Column(String)
    last_reviewed_at = Column(DateTime)

    repository = relationship("Repository", back_populates="pull_requests")
    issues = relationship("ReviewIssue", back_populates="pull_request")
