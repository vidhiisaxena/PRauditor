import json
from typing import List
from .types import DiffChunk, Issue
from .llm_client import chat


def _chunks_to_text(chunks: List[DiffChunk]) -> str:
    parts: list[str] = []
    for c in chunks:
        parts.append(f"File: {c.file_path}\n{c.patch}")
    return "\n\n".join(parts)


def _run_agent(chunks: List[DiffChunk], role_instructions: str, kind: str) -> List[Issue]:
    """
    Shared helper for all agents.
    """
    diff_text = _chunks_to_text(chunks)

    prompt = (
        role_instructions
        + "\n\n"
        "Return a JSON array of issues in this exact format:\n"
        '[{"file_path": "...", "line": 123, "severity": "major", '
        '"message": "short description", "suggestion": "optional fix"}]\n\n'
        "If there are no issues, return an empty JSON array []\n\n"
        "Diff:\n"
        f"{diff_text}"
    )

    raw = chat([{"role": "user", "content": prompt}], max_tokens=900)

    try:
        data = json.loads(raw)
    except Exception:
        # model might have added extra text; try to extract JSON very roughly
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                data = json.loads(raw[start : end + 1])
            except Exception:
                return []
        else:
            return []

    if not isinstance(data, list):
        return []

    issues: List[Issue] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        issues.append(
            Issue(
                file_path=item.get("file_path", ""),
                line=item.get("line"),
                kind=kind,
                severity=item.get("severity", "minor"),
                message=item.get("message", ""),
                suggestion=item.get("suggestion"),
            )
        )

    return issues


def logic_agent(chunks: List[DiffChunk]) -> List[Issue]:
    instructions = (
        "You review code changes for LOGIC and CORRECTNESS problems. "
        "Look for bugs, incorrect conditions, wrong edge-case handling, "
        "bad state transitions, missing null/None checks, and regressions."
        "Focus only on changed code."
    )
    return _run_agent(chunks, instructions, kind="logic")


def readability_agent(chunks: List[DiffChunk]) -> List[Issue]:
    instructions = (
        "You review code changes for READABILITY and MAINTAINABILITY. "
        "Look for unclear names, deeply nested code, missing comments around complex logic, "
        "and inconsistent style that makes the code hard to read."
        "Focus only on changed code."
    )
    return _run_agent(chunks, instructions, kind="readability")


def performance_agent(chunks: List[DiffChunk]) -> List[Issue]:
    instructions = (
        "You review code changes for PERFORMANCE issues. "
        "Look for obvious inefficiencies like unnecessary loops, repeated expensive calls, "
        "N+1 queries, or operations inside tight loops that could be moved out."
        "Focus only on changed code."
    )
    return _run_agent(chunks, instructions, kind="performance")


def security_agent(chunks: List[DiffChunk]) -> List[Issue]:
    instructions = (
        "You review code changes for SECURITY issues. "
        "Look for SQL injection, command injection, XSS, unsafe deserialization, "
        "hard-coded secrets, insecure use of crypto, and missing auth checks."
        "Focus only on changed code."
    )
    return _run_agent(chunks, instructions, kind="security")
