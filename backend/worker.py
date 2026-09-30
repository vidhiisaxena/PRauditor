import time
import signal
import sys
import logging
from concurrent.futures import ThreadPoolExecutor
from httpx import TimeoutException, HTTPStatusError

from backend.core.config import (
    JOB_MAX_ATTEMPTS, 
    JOB_BASE_RETRY_DELAY_SECONDS,
    JOB_STALE_TIMEOUT_MINUTES
)
import os

# Worker configs
WORKER_POLL_INTERVAL_SECONDS = int(os.getenv("WORKER_POLL_INTERVAL_SECONDS", "5"))
MAX_CONCURRENT_REVIEWS = int(os.getenv("MAX_CONCURRENT_REVIEWS", "3"))
STALE_RECOVERY_INTERVAL_MINUTES = int(os.getenv("STALE_RECOVERY_INTERVAL_MINUTES", "10"))

from backend.services import job_service
from backend.services.review_service import run_and_store_review
from backend.core.database import SessionLocal
from backend.models.pull_request import PullRequest
from backend.models.repository import Repository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

is_shutting_down = False

def handle_shutdown(signum, frame):
    global is_shutting_down
    logger.info("Shutdown signal received. Stopping job claims...")
    is_shutting_down = True

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

def is_transient_error(e: Exception) -> bool:
    """Classify exception to determine if it is transient/retryable."""
    if isinstance(e, TimeoutException):
        return True
    if isinstance(e, HTTPStatusError):
        # 429 Too Many Requests, or 5xx Server Error
        if e.response.status_code == 429 or e.response.status_code >= 500:
            return True
    # If using OpenAI SDK, we might catch openai.APIError etc here.
    msg = str(e).lower()
    if "timeout" in msg or "rate limit" in msg or "connection error" in msg:
        return True
    return False

def process_job(job: dict):
    """
    Executes a single review job.
    Designed to survive failures and isolate exceptions.
    """
    job_id = job["job_id"]
    pr_id = job["pull_request_id"]
    installation_id = job["installation_id"]
    job_head_sha = job["head_sha"]
    attempts = job["attempts"]
    
    logger.info(f"[Worker] JOB PROCESSING: job_id={job_id} attempt={attempts}")
    
    try:
        # Pre-flight SHA check and repository info load in a short DB session
        with SessionLocal() as db:
            pr = db.query(PullRequest).filter(PullRequest.id == pr_id).first()
            if not pr:
                raise ValueError(f"PullRequest {pr_id} not found")
            if pr.head_sha != job_head_sha:
                logger.info(f"[Worker] JOB SKIPPED AS STALE: job_id={job_id}. PR head_sha {pr.head_sha} != job head_sha {job_head_sha}")
                # Mark it completed because the newer job will take over, or skip it.
                # The prompt requested we use existing statuses.
                job_service.mark_completed(job_id)
                return
                
            repo = db.query(Repository).filter(Repository.id == pr.repo_id).first()
            if not repo:
                raise ValueError(f"Repository {pr.repo_id} not found")
            
            repo_full_name = repo.full_name
            pr_number = pr.pr_number
            pr_title = pr.title or ""

        # Execute AI Review (NO DB SESSION)
        # Passing job_head_sha ensures the post-review SHA check is performed
        run_and_store_review(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            pr_id=pr_id,
            installation_id=installation_id,
            job_head_sha=job_head_sha,
            pr_title=pr_title,
        )
        
        # Mark as completed in a short DB transaction
        job_service.mark_completed(job_id)
        logger.info(f"[Worker] JOB COMPLETED: job_id={job_id}")

    except Exception as e:
        logger.error(f"[Worker] Error processing job_id={job_id}: {type(e).__name__} - {str(e)}")
        if is_transient_error(e):
            # Exponential backoff
            delay = JOB_BASE_RETRY_DELAY_SECONDS * (2 ** (attempts - 1))
            # Cap delay to max 1 hour (3600 seconds)
            delay = min(delay, 3600)
            
            logger.info(f"[Worker] JOB RETRY: job_id={job_id}, attempt={attempts}, next_delay={delay}s")
            job_service.requeue_job(job_id, error_message=str(e), retry_delay_seconds=delay)
        else:
            logger.info(f"[Worker] JOB FAILED: job_id={job_id}, attempt={attempts} (Permanent error)")
            job_service.mark_failed(job_id, error_message=str(e))

def main():
    logger.info("Starting PR Auditor Durable Review Worker...")
    
    last_recovery_time = 0
    
    # Bounded ThreadPoolExecutor limits concurrent reviews
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REVIEWS) as executor:
        active_futures = set()
        
        while not is_shutting_down:
            # Clean up completed futures
            done = {fut for fut in active_futures if fut.done()}
            active_futures.difference_update(done)
            
            # Run stale job recovery periodically
            current_time = time.time()
            if current_time - last_recovery_time > (STALE_RECOVERY_INTERVAL_MINUTES * 60):
                recovered = job_service.recover_stuck_jobs()
                if recovered > 0:
                    logger.info(f"[Worker] STALE JOB RECOVERED: {recovered} jobs")
                last_recovery_time = current_time

            # Only claim jobs if we have capacity
            if len(active_futures) < MAX_CONCURRENT_REVIEWS:
                try:
                    job = job_service.claim_next_job()
                    if job:
                        logger.info(f"[Worker] JOB CLAIMED: job_id={job['job_id']}")
                        fut = executor.submit(process_job, job)
                        active_futures.add(fut)
                        continue  # Try to claim another immediately if capacity exists
                except Exception as e:
                    logger.error(f"[Worker] Failed to claim job: {e}")
            
            # Sleep if no jobs claimed or full capacity
            time.sleep(WORKER_POLL_INTERVAL_SECONDS)
            
    logger.info("Worker gracefully shut down. All active reviews completed.")

if __name__ == "__main__":
    main()
