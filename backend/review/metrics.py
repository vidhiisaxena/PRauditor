"""
Structured metrics logging for PRauditor review pipeline.

Logs key operational metrics (latency, static/LLM finding counts, escalation status)
without leaking sensitive repo source code or prompt contents.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def log_review_metrics(
    pr_id: Any,
    static_findings_count: int,
    llm_called: bool,
    llm_findings_count: int,
    final_findings_count: int,
    risk_level: str,
    changed_files_count: int,
    changed_lines: int,
    latency_ms: float,
) -> None:
    """Log structured review metrics to the logger."""
    metrics_data = {
        "pr_id": pr_id,
        "static_findings": static_findings_count,
        "llm_called": llm_called,
        "llm_findings": llm_findings_count if llm_called else 0,
        "final_findings": final_findings_count,
        "risk_level": risk_level,
        "changed_files": changed_files_count,
        "changed_lines": changed_lines,
        "latency_ms": round(latency_ms, 2),
    }

    logger.info(
        f"[Metrics] review_complete | PR: {pr_id} | files={changed_files_count} lines={changed_lines} "
        f"static={static_findings_count} llm_called={llm_called} llm_findings={metrics_data['llm_findings']} "
        f"final={final_findings_count} risk={risk_level} latency={metrics_data['latency_ms']}ms",
        extra=metrics_data,
    )
