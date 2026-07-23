import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.api import auth, dashboard, repos, pull_requests, webhook
from backend.core.config import CORS_ORIGINS
from backend.core.database import init_db

app = FastAPI(title="PRAuditor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(repos.router)
app.include_router(pull_requests.router)
app.include_router(webhook.router)

init_db()


@app.get("/")
def home():
    return {"status": "ok"}
