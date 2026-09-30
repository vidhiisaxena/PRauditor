import time
import logging
import requests
from typing import List, Dict

from backend.core.config import GPT_API_URL, GPT_API_KEY, GPT_MODEL

logger = logging.getLogger(__name__)


def chat(messages: List[Dict], max_tokens: int = 600, retries: int = 3) -> str:
    if not GPT_API_URL:
        raise RuntimeError("GPT_API_URL is not configured")

    payload = {
        "model": GPT_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
    }

    headers: Dict[str, str] = {}
    if GPT_API_KEY:
        headers["Authorization"] = f"Bearer {GPT_API_KEY}"

    last_exception = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(GPT_API_URL, json=payload, headers=headers, timeout=60)
            if r.status_code == 429 and attempt < retries:
                logger.warning(f"[LLM] Hit rate limit (429), retrying in {attempt * 3}s (attempt {attempt}/{retries})...")
                time.sleep(attempt * 3)
                continue
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            last_exception = e
            if attempt < retries:
                time.sleep(attempt * 2)
            else:
                raise

    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected error in chat()")
