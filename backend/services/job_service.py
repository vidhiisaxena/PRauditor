import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

from backend.core.database import SessionLocal, engine
from backend.models.review_job import ReviewJob
from backend.core.config import JOB_MAX_ATTEMPTS, JOB_STALE_TIMEOUT_MINUTES, JOB_BASE_RETRY_DELAY_SECONDS

logger = logging.getLogger(__name__)

def create_review_job(pull_request_id: int, installation_id: int, head_sha: str, db: SessionLocal = None) -> dict | None:
    """
    Creates a new review job if it doesn't already exist for this (installation_id, pull_request_id, head_sha).
    Returns the created/existing job as a dict, or None on failure.
    """
    def _do_create(session):
        try:
            with session.begin_nested():
                job = ReviewJob(
                    pull_request_id=pull_request_id,
                    installation_id=installation_id,
                    head_sha=head_sha,
                    status="queued"
                )
                session.add(job)
            
            # Note: flush happens at the end of begin_nested, committing the savepoint.
            # We don't commit the outer transaction here if we didn't create it.
            return {
                "id": job.id,
                "pull_request_id": job.pull_request_id,
                "installation_id": job.installation_id,
                "head_sha": job.head_sha,
                "status": job.status
            }
        except IntegrityError:
            # The savepoint is rolled back automatically.
            existing_job = session.query(ReviewJob).filter_by(
                pull_request_id=pull_request_id,
                installation_id=installation_id,
                head_sha=head_sha
            ).first()
            if existing_job:
                return {
                    "id": existing_job.id,
                    "pull_request_id": existing_job.pull_request_id,
                    "installation_id": existing_job.installation_id,
                    "head_sha": existing_job.head_sha,
                    "status": existing_job.status
                }
            return None
        except Exception as e:
            logger.error(f"Failed to create review job: {e}")
            raise

    if db is not None:
        return _do_create(db)
    else:
        with SessionLocal() as session:
            result = _do_create(session)
            session.commit()
            return result

def claim_next_job(max_attempts: int = JOB_MAX_ATTEMPTS) -> dict | None:
    """
    Atomically claims the next available queued job using SKIP LOCKED (if on PostgreSQL).
    Updates status to 'processing', increments attempts, and sets started_at.
    Returns scalar job data.
    """
    with SessionLocal() as db:
        now = datetime.now(timezone.utc)
        
        try:
            query = db.query(ReviewJob).filter(
                ReviewJob.status == "queued",
                ReviewJob.available_at <= now,
                ReviewJob.attempts < max_attempts
            ).order_by(ReviewJob.available_at.asc())
            
            if engine.dialect.name == "postgresql":
                query = query.with_for_update(skip_locked=True)
            else:
                pass
                # SQLite doesn't support SKIP LOCKED and can deadlock on with_for_update in some drivers

            job = query.first()
            if not job:
                return None
            
            # Atomic state transition
            job.status = "processing"
            job.attempts += 1
            job.started_at = now
            
            db.commit()
            db.refresh(job)
            
            return {
                "job_id": job.id,
                "pull_request_id": job.pull_request_id,
                "installation_id": job.installation_id,
                "head_sha": job.head_sha,
                "attempts": job.attempts,
                "status": job.status
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to claim next job: {e}")
            raise

def mark_completed(job_id: int) -> None:
    """
    Marks a processing job as completed.
    """
    with SessionLocal() as db:
        try:
            job = db.query(ReviewJob).filter_by(id=job_id).first()
            if job and job.status == "processing":
                job.status = "completed"
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to mark job completed: {e}")
            raise

def mark_failed(job_id: int, error_message: str) -> None:
    """
    Marks a processing job as failed permanently.
    """
    with SessionLocal() as db:
        try:
            job = db.query(ReviewJob).filter_by(id=job_id).first()
            if job and job.status == "processing":
                job.status = "failed"
                job.error_message = str(error_message)
                db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to mark job failed: {e}")
            raise

def requeue_job(job_id: int, error_message: str, max_attempts: int = JOB_MAX_ATTEMPTS, retry_delay_seconds: int = JOB_BASE_RETRY_DELAY_SECONDS) -> None:
    """
    Requeues a processing job for a retry, or marks it failed if max_attempts reached.
    Sets available_at to current UTC time + retry_delay_seconds.
    """
    with SessionLocal() as db:
        try:
            job = db.query(ReviewJob).filter_by(id=job_id).first()
            if job and job.status == "processing":
                job.error_message = str(error_message)
                
                # If attempt 3 (or whatever max is) just failed, we mark as failed, not requeue.
                if job.attempts >= max_attempts:
                    job.status = "failed"
                else:
                    job.status = "queued"
                    job.available_at = datetime.now(timezone.utc) + timedelta(seconds=retry_delay_seconds)
                    
                db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to requeue job: {e}")
            raise

def recover_stuck_jobs(timeout_minutes: int = JOB_STALE_TIMEOUT_MINUTES, max_attempts: int = JOB_MAX_ATTEMPTS) -> int:
    """
    Finds jobs stuck in 'processing' longer than timeout_minutes and either requeues them or fails them.
    Returns the number of recovered jobs.
    """
    with SessionLocal() as db:
        try:
            stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
            
            stuck_jobs = db.query(ReviewJob).filter(
                ReviewJob.status == "processing",
                ReviewJob.started_at <= stale_threshold
            ).all()
            
            count = 0
            for job in stuck_jobs:
                job.error_message = "Job recovered from stuck processing state."
                if job.attempts >= max_attempts:
                    job.status = "failed"
                else:
                    job.status = "queued"
                    job.available_at = datetime.now(timezone.utc)  # Available immediately
                count += 1
                
            if count > 0:
                db.commit()
            return count
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to recover stuck jobs: {e}")
            raise
