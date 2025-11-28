import json
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse

from backend.github_client import fetch_diff
from backend.github_webhook_utils import check_signature
from sqlalchemy.orm import Session
#from backend.review_agent import generate_review           
from backend.database import get_db
from . import models
from backend.schema import RepositoryOut, PullRequestOut, ReviewIssueOut



app= FastAPI()

@app.get("/")
def home():
    return {"status": "ok"}

@app.post("/github/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    check_signature(signature, body)

    try:
        data = json.loads(body.decode())
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = request.headers.get("X-GitHub-Event")
    action = data.get("action")

    if event == "pull_request" and action in ("opened", "reopened", "synchronize"):
        repo_full = data["repository"]["full_name"]      # "owner/repo"
        pr_info = data["pull_request"]
        pr_number = pr_info["number"]
        title = pr_info.get("title")
        state = pr_info.get("state")
        head_sha = pr_info.get("head", {}).get("sha") or pr_info.get("head", {}).get("ref")

        # Upsert Repository
        repo = (
            db.query(models.Repository)
            .filter(models.Repository.full_name == repo_full)
            .first()
        )
        if not repo:
            repo = models.Repository(full_name=repo_full)
            db.add(repo)
            db.commit()
            db.refresh(repo)

        # Upsert PullRequest (one record per repo+PR number)
        pr = (
            db.query(models.PullRequest)
            .filter(
                models.PullRequest.repo_id == repo.id,
                models.PullRequest.pr_number == pr_number,
            )
            .first()
        )
        if not pr:
            pr = models.PullRequest(
                repo_id=repo.id,
                pr_number=pr_number,
                title=title,
                state=state,
                head_sha=head_sha,
            )
            db.add(pr)
        else:
            pr.title = title
            pr.state = state
            pr.head_sha = head_sha

        db.commit()
        db.refresh(pr)

        # fetch diff, run agents, save ReviewIssue, post comment for later
        # diff = fetch_diff(repo_full, pr_number)
        # review_text = generate_review(diff)
        # post_comment(repo_full, pr_number, review_text)

    return JSONResponse({"ok": True})


# ---------- API: repositories ----------

@app.get("/api/repos", response_model=list[RepositoryOut])
def list_repositories(db: Session = Depends(get_db)):
    repos = db.query(models.Repository).order_by(models.Repository.full_name).all()
    return repos


# ---------- API: pull requests per repo ----------

@app.get("/api/repos/{repo_id}/prs", response_model=list[PullRequestOut])
def list_pull_requests(repo_id: int, db: Session = Depends(get_db)):
    q = (
        db.query(models.PullRequest)
        .filter(models.PullRequest.repo_id == repo_id)
        .order_by(models.PullRequest.pr_number.desc())
    )
    return q.all()


# ---------- API: issues for a PR ----------

@app.get("/api/prs/{pr_id}/issues", response_model=list[ReviewIssueOut])
def list_review_issues(pr_id: int, db: Session = Depends(get_db)):
    q = (
        db.query(models.ReviewIssue)
        .filter(models.ReviewIssue.pr_id == pr_id)
        .order_by(models.ReviewIssue.created_at.desc())
    )
    return q.all()
   






