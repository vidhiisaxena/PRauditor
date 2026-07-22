import os
from pathlib import Path
from dotenv import load_dotenv

# Repo root: backend/core/config.py -> parents[2] is the project root, where .env lives.
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

# GitHub App ID - can be string or int, will be converted to string for JWT
_app_id = os.getenv("GITHUB_APP_ID")
GITHUB_APP_ID = str(_app_id).strip() if _app_id else None

# Load private key: try direct content first, then file path
_private_key = os.getenv("GITHUB_PRIVATE_KEY")
if not _private_key:
    _key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH")
    if _key_path:
        _private_key = Path(_key_path).read_text()
    else:
        _private_key = None

# Handle escaped newlines in key
if _private_key and "\\n" in _private_key:
    _private_key = _private_key.replace("\\n", "\n")

# Ensure key has proper PEM format (strip whitespace but keep structure)
if _private_key:
    _private_key = _private_key.strip()

GITHUB_PRIVATE_KEY = os.getenv("GITHUB_PRIVATE_KEY", _private_key)
GITHUB_INSTALLATION_ID = os.getenv("GITHUB_INSTALLATION_ID")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
GITHUB_PERSONAL_TOKEN = os.getenv("GITHUB_PERSONAL_TOKEN")

GPT_API_URL = os.getenv("GPT_API_URL")
GPT_API_KEY = os.getenv("GPT_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o-mini")

DATABASE_URL = os.getenv("DATABASE_URL")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
ENV = os.getenv("ENV", "production")

# Comma-separated list of allowed browser origins for CORS. Defaults to local dev.
# In production set CORS_ORIGINS to your Vercel URL, e.g.
#   CORS_ORIGINS=https://pr-auditor.vercel.app,https://www.yourdomain.com
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "https://pr-auditor.vercel.app , https://prauditor-backend.onrender.com",
    ).split(",")
    if o.strip()
]
