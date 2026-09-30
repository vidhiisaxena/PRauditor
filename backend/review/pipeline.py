import logging
from typing import List

from backend.review.types import Issue
from backend.review.diff_parser import parse_unified_diff
from backend.review.agents import unified_review_agent

logger = logging.getLogger(__name__)


def run_review(
    diff_text: str,
    pr_title: str = "",
    pr_description: str = "",
    enclosing_context: str = "",
) -> List[Issue]:
    """
    Main entry point for the review pipeline.

    Parses the diff, runs a single unified LLM review call with chain-of-thought
    reasoning, and returns deduplicated, confidence-filtered issues.
    """
    chunks = parse_unified_diff(diff_text)

    if not chunks:
        logger.info("[Pipeline] No diff chunks to review")
        return []

    logger.info(f"[Pipeline] Reviewing {len(chunks)} file(s)...")

    issues = unified_review_agent(
        chunks,
        pr_title=pr_title,
        pr_description=pr_description,
        enclosing_context=enclosing_context,
    )

    deduplicated = _deduplicate(issues)
    logger.info(
        f"[Pipeline] {len(issues)} raw findings → {len(deduplicated)} after dedup"
    )

    return deduplicated


def _deduplicate(issues: List[Issue]) -> List[Issue]:
    """
    Deduplicate by (file_path, line, kind, message_prefix).
    When duplicates exist, keep the higher severity.
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
