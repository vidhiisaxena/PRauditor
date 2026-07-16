import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.api import dashboard, pull_request, repo, webhook
from backend.database import init_db

app = FastAPI(title="PRAuditor API")

origin=[
    "http://localhost:3000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(repo.router)
app.include_router(pull_request.router)
app.include_router(webhook.router)

init_db()

@app.get("/")
def home():
    return {"status": "ok"}