from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from backend.core.database import Base


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
