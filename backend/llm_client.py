import requests
from typing import List, Dict
from .config import GPT_API_URL, GPT_API_KEY, GPT_MODEL


def chat(messages: List[Dict], max_tokens: int = 600) -> str:
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

    r = requests.post(GPT_API_URL, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]
