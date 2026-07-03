#!/usr/bin/env python3
"""Run the FastAPI app with uvicorn ensuring project root is on sys.path.

Usage:
    python run_uvicorn.py

This avoids ModuleNotFoundError for the `backend` package when running
from different working directories or when the reloader spawns subprocesses.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

import uvicorn


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
