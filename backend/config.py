import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR=os.path.dirname(os.path.dirname(__file__))
ENV_PATH=os.path.join(BASE_DIR, '.env')
load_dotenv(ENV_PATH)

# GitHub App ID - can be string or int, will be converted to string for JWT
_app_id = os.getenv('GITHUB_APP_ID')
GITHUB_APP_ID = str(_app_id).strip() if _app_id else None

# Load private key: try direct content first, then file path
_private_key = os.getenv('GITHUB_PRIVATE_KEY')
if not _private_key:
    _key_path = os.getenv('GITHUB_PRIVATE_KEY_PATH')
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
    # Validate it looks like a PEM key
    if not _private_key.startswith("-----BEGIN"):
        # Try to fix if it's missing headers but has the key content
        if "BEGIN" not in _private_key and "END" not in _private_key:
            # This might be a base64-encoded key without headers - can't auto-fix
            pass

GITHUB_PRIVATE_KEY = _private_key
GITHUB_INSTALLATION_ID=os.getenv('GITHUB_INSTALLATION_ID')
GITHUB_WEBHOOK_SECRET=os.getenv('GITHUB_WEBHOOK_SECRET', "")
GITHUB_PERSONAL_TOKEN=os.getenv('GITHUB_PERSONAL_TOKEN')

GPT_API_URL=os.getenv('GPT_API_URL')
GPT_API_KEY=os.getenv('GPT_API_KEY')
GPT_MODEL=os.getenv("GPT_MODEL","gpt-4o-mini")

DATABASE_URL=os.getenv('DATABASE_URL')
HOST=os.getenv('HOST', '0.0.0.0')
PORT=int(os.getenv('PORT', 8000))
ENV=os.getenv('ENV', 'development')