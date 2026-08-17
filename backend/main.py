import sys
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.api import auth, dashboard, repos, pull_requests, webhook, installations
from backend.core.config import CORS_ORIGINS
from backend.core.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
app.include_router(installations.router)

init_db()

# Log registered routes at startup
logger.info("=" * 80)
logger.info("PRAuditor API Routes:")
for route in app.routes:
    if hasattr(route, "path") and hasattr(route, "methods"):
        logger.info(f"  {' | '.join(route.methods):20} {route.path}")
logger.info("=" * 80)


@app.get("/")
def home():
    return {"status": "ok"}
