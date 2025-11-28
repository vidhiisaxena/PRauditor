from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, unique=True, index=True)  # owner/repo

    pull_requests = relationship("PullRequest", back_populates="repository")


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


class ReviewIssue(Base):
    __tablename__ = "review_issues"

    id = Column(Integer, primary_key=True, index=True)
    pr_id = Column(Integer, ForeignKey("pull_requests.id"))

    file_path = Column(String)
    line = Column(Integer, nullable=True)
    kind = Column(String)        # logic / readability / performance / security
    severity = Column(String)    # info / minor / major / critical
    message = Column(Text)
    suggestion = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    pull_request = relationship("PullRequest", back_populates="issues")
