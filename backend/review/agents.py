import json
import logging
from typing import List, Dict, Any

from backend.review.types import DiffChunk, Issue
from backend.integrations.llm.client import chat

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """\
You are an expert senior software engineer performing a code review on a pull request.

Your job is to find genuine problems — bugs, performance issues, security vulnerabilities, \
and meaningful redundancy — in the CHANGED code only.

## Rules

1. ONLY flag issues in code that was ADDED or MODIFIED (lines starting with +).
   Never flag deleted code or unchanged context lines.
2. Every issue MUST include `evidence` — quote the exact problematic code.
3. Every issue MUST have a concrete `impact` — what breaks, what's slow, what's unsafe.
4. Do NOT report style preferences, naming opinions, or missing comments \
   unless they create a genuine maintainability risk.
5. If you are uncertain, set confidence to "low". Low-confidence findings will be discarded.
6. It is completely acceptable to return empty arrays. \
   A clean PR with no issues is a valid outcome.
7. Fewer high-quality findings are always better than many mediocre ones.

## Severity Guide

- **critical**: Will cause data loss, security breach, or crash in production.
- **major**: Likely bug, significant performance regression, or real security risk.
- **minor**: Potential issue under specific conditions, or meaningful optimization.
- **info**: Observation worth noting. Use sparingly.

## Confidence Guide

- **high**: You can see the bug/issue directly in the code with clear evidence.
- **medium**: Likely an issue but depends on context you can't fully see.
- **low**: Possible issue but you're guessing. These will be filtered out.\
"""


USER_PROMPT_TEMPLATE = """\
Analyze this pull request and report issues in 4 categories: \
logic, performance, security, and readability.

Think step-by-step before producing findings.

{context_section}

## Diff

```
{diff_text}
```

## Response Format

Return ONLY a valid JSON object (no markdown fences, no extra text) with this exact structure:

{{
  "summary": "1-2 sentence description of what this PR does",
  "reasoning": "Your step-by-step analysis of the changes, what could go wrong, and why",
  "findings": {{
    "logic": [
      {{
        "file_path": "path/to/file.py",
        "line": 42,
        "severity": "major",
        "message": "Clear description of the problem",
        "evidence": "exact code snippet from the diff",
        "impact": "what happens as a result of this issue",
        "suggestion": "how to fix it",
        "confidence": "high"
      }}
    ],
    "performance": [],
    "security": [],
    "readability": []
  }}
}}

If there are no issues in a category, return an empty array for that category.\
"""


def _build_context_section(
    pr_title: str = "",
    pr_description: str = "",
    enclosing_context: str = "",
) -> str:
    """Build the optional context block for the prompt."""
    parts = []

    if pr_title:
        parts.append(f"**PR Title:** {pr_title}")
    if pr_description:
        # Truncate very long descriptions
        desc = pr_description[:500]
        if len(pr_description) > 500:
            desc += "..."
        parts.append(f"**PR Description:** {desc}")
    if enclosing_context:
        parts.append(f"## Enclosing Context\n\n{enclosing_context}")

    if parts:
        return "## PR Context\n\n" + "\n\n".join(parts)
    return ""


def _chunks_to_text(chunks: List[DiffChunk]) -> str:
    """Convert diff chunks to a single text block for the prompt."""
    parts: list[str] = []
    for c in chunks:
        parts.append(f"File: {c.file_path}\n{c.patch}")
    return "\n\n".join(parts)


def _extract_json(raw: str) -> Any:
    """
    Extract JSON from LLM response, handling markdown fences and extra text.
    """
    text = raw.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        # Remove opening fence (```json or ```)
        first_newline = text.index("\n")
        text = text[first_newline + 1:]
        # Remove closing fence
        if text.endswith("```"):
            text = text[:-3].strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def _parse_findings(data: dict) -> List[Issue]:
    """
    Parse the structured LLM response into a flat list of Issue objects.
    Filters out low-confidence findings.
    """
    findings = data.get("findings", {})
    issues: List[Issue] = []

    valid_kinds = {"logic", "performance", "security", "readability"}

    for kind, items in findings.items():
        if kind not in valid_kinds:
            continue
        if not isinstance(items, list):
            continue

        for item in items:
            if not isinstance(item, dict):
                continue

            # Filter out low-confidence findings
            confidence = item.get("confidence", "low").lower()
            if confidence == "low":
                logger.info(
                    f"[Agent] Filtered low-confidence finding: "
                    f"{item.get('file_path', '?')}:{item.get('line', '?')} - "
                    f"{item.get('message', '?')[:80]}"
                )
                continue

            # Filter readability issues that are just style opinions (info severity)
            if kind == "readability" and item.get("severity", "info") == "info":
                continue

            # Build message with evidence and impact if available
            message = item.get("message", "")
            evidence = item.get("evidence", "")
            impact = item.get("impact", "")

            if evidence or impact:
                enriched_parts = [message]
                if evidence:
                    enriched_parts.append(f"Evidence: `{evidence}`")
                if impact:
                    enriched_parts.append(f"Impact: {impact}")
                message = " | ".join(enriched_parts)

            issues.append(
                Issue(
                    file_path=item.get("file_path", ""),
                    line=item.get("line"),
                    kind=kind,
                    severity=item.get("severity", "minor"),
                    message=message,
                    suggestion=item.get("suggestion"),
                )
            )

    return issues


def unified_review_agent(
    chunks: List[DiffChunk],
    pr_title: str = "",
    pr_description: str = "",
    enclosing_context: str = "",
) -> List[Issue]:
    """
    Single-call unified code review agent.

    Sends one LLM request that analyzes the diff across all 4 categories
    (logic, performance, security, readability) using chain-of-thought reasoning.
    Requires evidence and confidence for each finding.
    """
    diff_text = _chunks_to_text(chunks)
    if not diff_text.strip():
        return []

    context_section = _build_context_section(pr_title, pr_description, enclosing_context)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        context_section=context_section,
        diff_text=diff_text,
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    logger.info("[Agent] Sending unified review request to LLM...")

    try:
        # Allow more output tokens for the structured response with reasoning
        raw = chat(messages, max_tokens=2000)
    except Exception as e:
        logger.error(f"[Agent] LLM call failed: {type(e).__name__}: {e}")
        raise

    logger.info(f"[Agent] LLM response received ({len(raw)} chars)")

    data = _extract_json(raw)
    if data is None:
        logger.warning("[Agent] Failed to parse LLM response as JSON")
        logger.debug(f"[Agent] Raw response: {raw[:500]}")
        return []

    if not isinstance(data, dict):
        logger.warning(f"[Agent] LLM returned {type(data).__name__}, expected dict")
        return []

    # Log the summary and reasoning for debugging
    summary = data.get("summary", "")
    reasoning = data.get("reasoning", "")
    if summary:
        logger.info(f"[Agent] PR Summary: {summary}")
    if reasoning:
        logger.info(f"[Agent] Reasoning: {reasoning[:200]}...")

    issues = _parse_findings(data)
    logger.info(f"[Agent] {len(issues)} findings passed filters")

    return issues


# ──────────────────────────────────────────────────────────────────────
# Legacy agents — kept for backward compatibility and A/B testing.
# These will be removed once the unified agent is validated.
# ──────────────────────────────────────────────────────────────────────

def _run_agent(chunks: List[DiffChunk], role_instructions: str, kind: str) -> List[Issue]:
    """
    Shared helper for legacy agents.
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
