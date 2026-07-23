from backend.api.auth import router as auth_router
from backend.api.dashboard import router as dashboard_router
from backend.api.repos import router as repositories_router
from backend.api.pull_requests import router as pull_requests_router
from backend.api.webhook import router as webhook_router

__all__ = [
    "auth_router",
    "dashboard_router",
    "repositories_router",
    "pull_requests_router",
    "webhook_router",
]
