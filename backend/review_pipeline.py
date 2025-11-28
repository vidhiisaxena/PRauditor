from typing import List
from backend.types import Issue
from backend.diff_parser import parse_unified_diff
from backend.agents import (
    logic_agent,
    readability_agent,
    performance_agent,
    security_agent,
)


def run_review(diff_text: str) -> List[Issue]:
    """
    Main entry point for the review pipeline.
    """
    chunks = parse_unified_diff(diff_text)

    if not chunks:
        return []

    # For very large diffs, you might want to truncate here.
    # For now, use all chunks.

    issues: List[Issue] = []
    issues.extend(logic_agent(chunks))
    issues.extend(readability_agent(chunks))
    issues.extend(performance_agent(chunks))
    issues.extend(security_agent(chunks))

    return _merge_similar(issues)


def _merge_similar(issues: List[Issue]) -> List[Issue]:
    """
    Simple dedupe by (file_path, line, kind, message prefix).
    """
    seen: dict[tuple, Issue] = {}
    for it in issues:
        key = (
            it.file_path,
            it.line,
            it.kind,
            (it.message[:80] if it.message else ""),
        )
        if key in seen:
            # choose higher severity if they differ
            existing = seen[key]
            existing.severity = _max_severity(existing.severity, it.severity)
        else:
            seen[key] = it
    return list(seen.values())


def _max_severity(a: str, b: str) -> str:
    order = {"info": 0, "minor": 1, "major": 2, "critical": 3}
    ia = order.get(a, 1)
    ib = order.get(b, 1)
    return a if ia >= ib else b
