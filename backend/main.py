import json
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session

from backend.database import get_db
from backend import models

from backend.github_webhook_utils import check_signature
from backend.github_client import fetch_pr_diff, post_pr_comment

from backend.review_pipeline import run_review
from backend.markdown import issues_to_markdown

from backend.schema import RepositoryOut, PullRequestOut, ReviewIssueOut


app = FastAPI()


@app.get("/")
def home():
    return {"status": "ok"}


# -----------------------------------------------------------
#  GITHUB WEBHOOK: PR -> DIFF -> REVIEW -> DB -> COMMENT
# -----------------------------------------------------------
@app.post("/github/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        payload = await request.json()

    elif "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        if "payload" not in form:
            return {"ok": False, "error": "No payload in form"}
        payload = json.loads(form["payload"])

    else:
        return {"ok": False, "error": f"Unsupported content type: {content_type}"}

    print("🎉 Parsed payload:", payload["action"])
    
    
    # 1) Validate signature (pure function)
    if not check_signature(signature, raw_body):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 2) Event type
    event = request.headers.get("X-GitHub-Event", "")
    content_type = request.headers.get("content-type", "")

    # Handle ping explicitly
    if event == "ping":
        return JSONResponse({"ok": True, "note": "Ping received"})

    # 3) Parse body depending on content type
    if content_type.startswith("application/x-www-form-urlencoded"):
        form = await request.form()
        payload_str = form.get("payload")
        if not payload_str:
            raise HTTPException(status_code=400, detail="Missing payload field")
        try:
            data = json.loads(payload_str)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
    else:
        # GitHub App / JSON style
        try:
            data = json.loads(raw_body.decode("utf-8"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

    action = data.get("action")

    # We only care about pull_request events
    if event != "pull_request":
        return {"ignored": True}

    if action not in ("opened", "reopened", "synchronize"):
        return {"ignored": True}

    # ----------------- Extract PR info -----------------
    repo_full = data["repository"]["full_name"]  # "owner/repo"
    pr_info = data["pull_request"]

    pr_number = pr_info["number"]
    title = pr_info.get("title")
    state = pr_info.get("state")
    head_sha = pr_info.get("head", {}).get("sha")

    # ----------------- Upsert Repository -----------------
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

    # ----------------- Upsert PullRequest -----------------
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
        db.commit()
        db.refresh(pr)
    else:
        pr.title = title
        pr.state = state
        pr.head_sha = head_sha
        db.commit()

    # ----------------- Fetch diff -----------------
    diff_text = fetch_pr_diff(repo_full, pr_number)

    # ----------------- Run multi-agent review -----------------
    issues = run_review(diff_text)

    # ----------------- Save issues to DB -----------------
    db.query(models.ReviewIssue).filter(
        models.ReviewIssue.pr_id == pr.id
    ).delete()
    db.commit()

    for it in issues:
        db_issue = models.ReviewIssue(
            pr_id=pr.id,
            file_path=it.file_path,
            line=it.line,
            kind=it.kind,
            severity=it.severity,
            message=it.message,
            suggestion=it.suggestion,
        )
        db.add(db_issue)

    db.commit()

    # ----------------- Post review comment to PR -----------------
    markdown_comment = issues_to_markdown(issues)
    post_pr_comment(repo_full, pr_number, markdown_comment)

    return JSONResponse({"reviewed": True, "issues": len(issues)})


# -----------------------------------------------------------
#                 READ APIs FOR FRONTEND
# -----------------------------------------------------------

@app.get("/api/repos", response_model=list[RepositoryOut])
def list_repositories(db: Session = Depends(get_db)):
    return (
        db.query(models.Repository)
        .order_by(models.Repository.full_name)
        .all()
    )


@app.get("/api/repos/{repo_id}/prs", response_model=list[PullRequestOut])
def list_pull_requests(repo_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.PullRequest)
        .filter(models.PullRequest.repo_id == repo_id)
        .order_by(models.PullRequest.pr_number.desc())
        .all()
    )


@app.get("/api/prs/{pr_id}/issues", response_model=list[ReviewIssueOut])
def list_review_issues(pr_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.ReviewIssue)
        .filter(models.ReviewIssue.pr_id == pr_id)
        .order_by(models.ReviewIssue.created_at.desc())
        .all()
    )
