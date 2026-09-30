"""
Deterministic PR summarizer and escalation engine for PRauditor.

Generates human-readable summaries, classifies domains, evaluates risk level,
and decides whether escalation to the LLM is required — with zero LLM cost.
"""

from dataclasses import dataclass
from typing import List, Optional, Set
import re
import os

from backend.review.types import ReviewContext, ChangedFile
from backend.review.static_analyzers import StaticFinding


@dataclass
class PRSummary:
    description: str           # e.g. "Modifies 3 files in backend/services/. Adds 2 new functions. Changes database query logic."
    changed_domains: List[str] # ["database", "auth", "api"]
    risk_level: str            # "low", "medium", "high"
    static_finding_count: int
    needs_llm: bool            # escalation decision
    llm_reason: Optional[str]  # why LLM is needed, if applicable


DOMAIN_RULES = [
    ("auth", re.compile(r"(?:^|[\W_])(auth|login|session|token|oauth|credential|jwt|password)(?:$|[\W_])", re.IGNORECASE)),
    ("database", re.compile(r"(?:^|[\W_])(db|model|models|migration|migrations|query|sql|orm|repository|schema|database)(?:$|[\W_])", re.IGNORECASE)),
    ("api", re.compile(r"(?:^|[\W_])(api|route|routes|endpoint|endpoints|view|views|controller|router|handler|url)(?:$|[\W_])", re.IGNORECASE)),
    ("test", re.compile(r"(?:^|[\W_])(test|tests|spec|specs|fixture|mock|testing)(?:$|[\W_])", re.IGNORECASE)),
    ("config", re.compile(r"(?:^|[\W_])(config|settings|env|dockerfile|yaml|yml|ini|toml)(?:$|[\W_])|\.(?:ya?ml|env|ini|toml)$", re.IGNORECASE)),
    ("docs", re.compile(r"(?:^|[\W_])(readme|docs?|license|changelog)(?:$|[\W_])|\.md$", re.IGNORECASE)),
    ("styling", re.compile(r"(?:^|[\W_])(css|scss|style|styles|theme|tailwind|less)(?:$|[\W_])|\.(?:css|scss|less)$", re.IGNORECASE)),
    ("dependencies", re.compile(r"(package\.json|requirements\.txt|cargo\.toml|pyproject\.toml|go\.mod|gemfile)", re.IGNORECASE)),
]

PAYMENT_KEYWORDS = re.compile(r"\b(payment|billing|stripe|invoice|checkout|subscription)\b", re.IGNORECASE)

CONTROL_FLOW_RE = re.compile(r"\b(if\s+|elif\s+|else:|for\s+|while\s+|try:|except|match\s+|case\s+)\b")

LOW_RISK_DOMAINS = {"docs", "config", "test", "styling", "dependencies"}


def _classify_domains(files: List[ChangedFile]) -> List[str]:
    """Classify changed files into domains based on paths and filenames."""
    detected: Set[str] = set()

    for f in files:
        path = f.path.replace("\\", "/").lower()
        filename = os.path.basename(path)

        # Check documentation first
        if path.endswith(".md") or "/docs/" in f"/{path}" or "/doc/" in f"/{path}":
            detected.add("docs")
            continue

        # Check tests next
        if "/tests/" in f"/{path}" or "/test/" in f"/{path}" or filename.startswith("test_") or filename.endswith("_test.py"):
            detected.add("test")
            continue

        # Check styling
        if path.endswith((".css", ".scss", ".less", ".sass")):
            detected.add("styling")
            continue

        # Check dependencies
        if filename in ("package.json", "requirements.txt", "cargo.toml", "pyproject.toml", "go.mod", "gemfile"):
            detected.add("dependencies")
            continue

        # Check config
        if filename.startswith(".env") or path.endswith((".yaml", ".yml", ".toml", ".ini")) or "dockerfile" in filename:
            detected.add("config")
            continue

        for domain, pattern in DOMAIN_RULES:
            if pattern.search(path) or pattern.search(filename):
                detected.add(domain)

    # Sort deterministically
    return sorted(list(detected))


def _has_control_flow_changes(files: List[ChangedFile]) -> bool:
    """Check if added lines modify control flow statements."""
    for f in files:
        for hunk in f.hunks:
            for line in hunk.lines:
                if line.line_type == "add":
                    if CONTROL_FLOW_RE.search(line.content):
                        return True
    return False


def _check_payment_logic(files: List[ChangedFile]) -> bool:
    """Check if diff touches payment or billing logic."""
    for f in files:
        if PAYMENT_KEYWORDS.search(f.path):
            return True
        for hunk in f.hunks:
            for line in hunk.lines:
                if line.line_type == "add" and PAYMENT_KEYWORDS.search(line.content):
                    return True
    return False


def generate_pr_summary(
    context: ReviewContext,
    static_findings: List[StaticFinding],
) -> PRSummary:
    """
    Generate a deterministic PRSummary and make an escalation decision.
    """
    files = context.files
    domains = _classify_domains(files)

    total_additions = context.total_additions or sum(f.additions for f in files)
    total_deletions = context.total_deletions or sum(f.deletions for f in files)
    total_lines = total_additions + total_deletions

    # Check finding severities
    has_critical_or_major_finding = any(
        f.severity in ("critical", "major") for f in static_findings
    )
    has_minor_finding = any(f.severity == "minor" for f in static_findings)

    touches_auth = "auth" in domains
    touches_db = "database" in domains
    touches_api = "api" in domains
    touches_payment = _check_payment_logic(files)
    touches_control_flow = _has_control_flow_changes(files)

    # Determine risk level
    if (
        touches_auth
        or touches_db
        or touches_payment
        or has_critical_or_major_finding
        or total_lines >= 500
    ):
        risk_level = "high"
    elif (
        touches_api
        or has_minor_finding
        or (100 <= total_lines < 500)
        or any(d not in LOW_RISK_DOMAINS for d in domains)
    ):
        risk_level = "medium"
    else:
        risk_level = "low"

    # Determine whether only low-risk files/domains were modified
    is_only_low_risk_domains = bool(domains) and all(d in LOW_RISK_DOMAINS for d in domains)
    has_non_trivial_logic = any(d not in LOW_RISK_DOMAINS for d in domains) or (not domains and total_lines > 0)

    # Count distinct directory modules
    top_dirs = {
        f.path.split("/")[0] if "/" in f.path else "."
        for f in files
        if not any(d in f.path for d in ("docs", ".github", "tests"))
    }
    has_multiple_modules = len(top_dirs) > 1

    # Escalation decision
    needs_llm = False
    llm_reasons: List[str] = []

    if risk_level == "high":
        needs_llm = True
        if touches_auth:
            llm_reasons.append("changes authentication or security logic")
        if touches_db:
            llm_reasons.append("changes database queries or schema")
        if total_lines >= 500:
            llm_reasons.append("large PR exceeding 500 changed lines")
        if has_critical_or_major_finding:
            llm_reasons.append("critical or major static findings require contextual evaluation")
        if not llm_reasons:
            llm_reasons.append("high risk score")

    elif risk_level == "medium":
        needs_llm = True
        if touches_api:
            llm_reasons.append("modifies API endpoints or public routes")
        elif touches_control_flow:
            llm_reasons.append("modifies branching or control flow logic")
        elif has_multiple_modules:
            llm_reasons.append("modifies multiple interconnected modules")
        else:
            llm_reasons.append("medium risk business logic change")

    elif has_non_trivial_logic and touches_control_flow:
        needs_llm = True
        llm_reasons.append("contains non-trivial logic and control flow changes")

    # Override: if all domains are low risk, risk is low, and static findings are clean/clear-cut
    if is_only_low_risk_domains and risk_level == "low":
        needs_llm = False
        llm_reasons = []

    llm_reason = "; ".join(llm_reasons) if needs_llm else None

    # Construct descriptive summary sentence
    file_count = len(files)
    file_str = f"Modifies {file_count} file{'s' if file_count != 1 else ''}"
    if total_lines > 0:
        file_str += f" (+{total_additions}, -{total_deletions})"

    domain_str = f" in {', '.join(domains)}" if domains else ""
    finding_str = f". {len(static_findings)} static finding(s) detected" if static_findings else ". No static pattern anomalies detected"
    description = f"{file_str}{domain_str}{finding_str}. Risk level: {risk_level}."

    return PRSummary(
        description=description,
        changed_domains=domains,
        risk_level=risk_level,
        static_finding_count=len(static_findings),
        needs_llm=needs_llm,
        llm_reason=llm_reason,
    )
