"""
Deterministic-first review pipeline orchestrator for PRauditor.

Executes fast deterministic static analysis and PR summarization first.
Escalates to the unified LLM agent ONLY when required by non-trivial code changes,
passing deterministic findings as structured hints.
"""

import time
import logging
from typing import List, Dict, Tuple, Optional, Any

from backend.review.types import Issue, DiffChunk, ReviewContext, PRMetadata
from backend.review.diff_parser import parse_unified_diff_extended, parse_unified_diff
from backend.review.context_builder import build_review_context
from backend.review.static_analyzers import run_static_analysis, StaticFinding
from backend.review.pr_summarizer import generate_pr_summary, PRSummary
from backend.review.metrics import log_review_metrics
from backend.review.agents import unified_review_agent

logger = logging.getLogger(__name__)


def static_finding_to_issue(finding: StaticFinding) -> Issue:
    """Convert a deterministic StaticFinding into the standard Issue dataclass."""
    message = finding.title
    if finding.evidence:
        message += f" | Evidence: `{finding.evidence}`"
    if finding.message:
        message += f" | {finding.message}"

    return Issue(
        file_path=finding.file_path,
        line=finding.line,
        kind=finding.category,
        severity=finding.severity,
        message=message,
        suggestion=finding.suggestion,
    )


def merge_findings(static_issues: List[Issue], llm_issues: List[Issue]) -> List[Issue]:
    """
    Merge deterministic static findings with LLM findings.
    - If static and LLM report on same file+line with matching category: keep more detailed finding (usually LLM).
    - If they report different categories on same line: keep both.
    - Deduplicate by (file_path, line, kind).
    """
    # Group static issues by (file_path, line)
    static_by_loc: Dict[Tuple[str, Optional[int]], List[Issue]] = {}
    for si in static_issues:
        static_by_loc.setdefault((si.file_path, si.line), []).append(si)

    merged: List[Issue] = []
    used_static_keys: set = set()

    for li in llm_issues:
        loc = (li.file_path, li.line)
        if loc in static_by_loc:
            # Check if there is an agreeing static issue
            agreeing = [s for s in static_by_loc[loc] if s.kind == li.kind]
            if agreeing:
                # Same category: prefer LLM if it has more detail, else static
                best_static = agreeing[0]
                used_static_keys.add((best_static.file_path, best_static.line, best_static.kind))
                if len(li.message) >= len(best_static.message):
                    # Keep LLM finding but carry over higher severity if applicable
                    li.severity = _max_severity(best_static.severity, li.severity)
                    merged.append(li)
                else:
                    merged.append(best_static)
            else:
                # Disagreeing category on same line: keep LLM finding
                merged.append(li)
        else:
            merged.append(li)

    # Add remaining static issues that were not superseded
    for si in static_issues:
        key = (si.file_path, si.line, si.kind)
        if key not in used_static_keys:
            merged.append(si)

    return _deduplicate(merged)


def _deduplicate(issues: List[Issue]) -> List[Issue]:
    """
    Deduplicate by (file_path, line, kind).
    When duplicates exist, preserve the higher severity.
    """
    seen: Dict[Tuple, Issue] = {}
    for it in issues:
        key = (it.file_path, it.line, it.kind)
        if key in seen:
            existing = seen[key]
            existing.severity = _max_severity(existing.severity, it.severity)
            if len(it.message) > len(existing.message):
                existing.message = it.message
            if it.suggestion and not existing.suggestion:
                existing.suggestion = it.suggestion
        else:
            seen[key] = it
    return list(seen.values())


def _max_severity(a: str, b: str) -> str:
    order = {"suggestion": 0, "info": 0, "minor": 1, "major": 2, "critical": 3}
    ia = order.get(a, 1)
    ib = order.get(b, 1)
    return a if ia >= ib else b


def run_review(
    diff_text: str,
    pr_title: str = "",
    pr_description: str = "",
    enclosing_context: str = "",
    pr_id: Any = "local",
) -> List[Issue]:
    """
    Deterministic-first review pipeline entry point.

    1. Parse diff into structured ChangedFiles
    2. Run fast deterministic static analysis (<100ms)
    3. Generate deterministic PR summary and evaluate risk
    4. If escalation is not needed: return static findings ($0.00 LLM cost)
    5. If escalation is needed: call LLM with static hints + merge results
    """
    start_time = time.time()

    if not diff_text or not diff_text.strip():
        logger.info("[Pipeline] Empty diff provided, skipping review")
        return []

    # 1. Parse diff into structured context
    metadata = PRMetadata(title=pr_title, description=pr_description)
    context: ReviewContext = build_review_context(diff_text, metadata=metadata)
    changed_files = context.files

    if not changed_files:
        logger.info("[Pipeline] No changed files detected in diff")
        return []

    # 2. Run static analysis
    static_findings: List[StaticFinding] = run_static_analysis(changed_files)
    static_issues: List[Issue] = [static_finding_to_issue(f) for f in static_findings]
    logger.info(f"[Pipeline] Static analysis completed: {len(static_findings)} finding(s)")

    # 3. Generate PR summary and determine escalation
    summary: PRSummary = generate_pr_summary(context, static_findings)
    logger.info(
        f"[Pipeline] PR Summary: {summary.description} | Needs LLM: {summary.needs_llm} "
        f"({summary.llm_reason or 'No escalation'})"
    )

    total_changed_lines = context.total_additions + context.total_deletions
    llm_findings: List[Issue] = []

    # 4. If escalation to LLM is NOT needed: return static findings
    if not summary.needs_llm:
        final_issues = _deduplicate(static_issues)
        elapsed_ms = (time.time() - start_time) * 1000
        log_review_metrics(
            pr_id=pr_id,
            static_findings_count=len(static_findings),
            llm_called=False,
            llm_findings_count=0,
            final_findings_count=len(final_issues),
            risk_level=summary.risk_level,
            changed_files_count=len(changed_files),
            changed_lines=total_changed_lines,
            latency_ms=elapsed_ms,
        )
        logger.info(
            f"[Pipeline] Zero-LLM path complete: {len(final_issues)} finding(s) in {elapsed_ms:.1f}ms ($0.00 cost)"
        )
        return final_issues

    # 5. Escalation: call LLM with static hints & summary
    chunks = parse_unified_diff(diff_text)
    logger.info(
        f"[Pipeline] Escalating to LLM with {len(static_findings)} static hint(s)..."
    )

    try:
        llm_findings = unified_review_agent(
            chunks=chunks,
            pr_title=pr_title,
            pr_description=pr_description,
            enclosing_context=enclosing_context,
            static_findings=static_findings,
            pr_summary=summary,
        )
    except Exception as e:
        logger.error(f"[Pipeline] LLM call failed during escalation: {e}. Falling back to static findings.")
        llm_findings = []

    # Merge static + LLM findings
    final_issues = merge_findings(static_issues, llm_findings)
    elapsed_ms = (time.time() - start_time) * 1000

    log_review_metrics(
        pr_id=pr_id,
        static_findings_count=len(static_findings),
        llm_called=True,
        llm_findings_count=len(llm_findings),
        final_findings_count=len(final_issues),
        risk_level=summary.risk_level,
        changed_files_count=len(changed_files),
        changed_lines=total_changed_lines,
        latency_ms=elapsed_ms,
    )

    logger.info(
        f"[Pipeline] Review complete: {len(static_findings)} static + {len(llm_findings)} LLM → "
        f"{len(final_issues)} final finding(s) in {elapsed_ms:.1f}ms"
    )

    return final_issues
