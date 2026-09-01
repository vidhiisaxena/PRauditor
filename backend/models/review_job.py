from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Index, UniqueConstraint, func
from sqlalchemy.orm import relationship

from backend.core.database import Base


class ReviewJob(Base):
    __tablename__ = "review_jobs"

    id = Column(Integer, primary_key=True, index=True)
    pull_request_id = Column(Integer, ForeignKey("pull_requests.id"), nullable=False, index=True)
    installation_id = Column(Integer, nullable=False, index=True)
    head_sha = Column(String, nullable=False)
    
    status = Column(String, nullable=False, default="queued") # queued, processing, completed, failed
    attempts = Column(Integer, nullable=False, default=0)
    
    available_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    pull_request = relationship("PullRequest", back_populates="review_jobs")

    __table_args__ = (
        UniqueConstraint('installation_id', 'pull_request_id', 'head_sha', name='uq_review_job_inst_pr_sha'),
        Index('ix_review_jobs_status_available_at', 'status', 'available_at'),
    )
