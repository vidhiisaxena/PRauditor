"""Shared FastAPI dependencies for the API routers."""

from backend.core.database import get_db

__all__ = ["get_db"]
