import os
import re
from typing import Callable, Optional, List

from backend.review.types import ReviewContext, PRMetadata, ChangedFile
from backend.review.diff_parser import parse_unified_diff_extended

# Configurable Context Limits
MAX_CONTEXT_FILES = int(os.getenv("MAX_CONTEXT_FILES", "30"))
MAX_CONTEXT_LINES_PER_FILE = int(os.getenv("MAX_CONTEXT_LINES_PER_FILE", "500"))
MAX_TOTAL_CONTEXT_LINES = int(os.getenv("MAX_TOTAL_CONTEXT_LINES", "3000"))

# Default patterns for ignored lockfiles and generated assets
IGNORED_PATTERNS = [
    r"package-lock\.json$",
    r"yarn\.lock$",
    r"pnpm-lock\.yaml$",
    r"poetry\.lock$",
    r"Cargo\.lock$",
    r"Pipfile\.lock$",
    r"\.min\.js$",
    r"\.min\.css$",
    r"\.map$",
    r"\.pb\.go$",
    r"_pb2\.py$",
]


def is_ignored_file(path: str) -> bool:
    """Checks whether a file path matches ignored lockfile or generated patterns."""
    for pattern in IGNORED_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE):
            return True
    return False


def build_review_context(
    diff_text: str,
    metadata: Optional[PRMetadata] = None,
    file_content_fetcher: Optional[Callable[[str, str], Optional[str]]] = None,
) -> ReviewContext:
    """
    Builds a bounded, SHA-correct ReviewContext object from unified diff text and PR metadata.
    
    `file_content_fetcher`: Optional callable `fetch(path, sha) -> Optional[str]` that retrieves
    full file content at HEAD SHA for enclosing context extraction.
    """
    if metadata is None:
        metadata = PRMetadata()

    files = parse_unified_diff_extended(diff_text)
    ctx = ReviewContext(metadata=metadata)

    total_additions = 0
    total_deletions = 0
    total_lines = 0

    if len(files) > MAX_CONTEXT_FILES:
        ctx.truncated = True
        ctx.truncation_reason = f"Exceeded maximum file limit ({len(files)} > {MAX_CONTEXT_FILES})"
        files = files[:MAX_CONTEXT_FILES]

    for f in files:
        if is_ignored_file(f.path):
            f.is_ignored = True

        total_additions += f.additions
        total_deletions += f.deletions

        if f.is_binary or f.is_ignored:
            ctx.files.append(f)
            continue

        # Truncate hunks if file context exceeds MAX_CONTEXT_LINES_PER_FILE
        file_line_count = sum(len(h.lines) for h in f.hunks)
        if file_line_count > MAX_CONTEXT_LINES_PER_FILE:
            ctx.truncated = True
            ctx.truncation_reason = f"File {f.path} exceeded per-file line limit ({file_line_count} > {MAX_CONTEXT_LINES_PER_FILE})"
            _truncate_file_hunks(f, MAX_CONTEXT_LINES_PER_FILE)

        # Build enclosing context
        enclosing = None
        if file_content_fetcher and metadata.head_sha:
            try:
                full_content = file_content_fetcher(f.path, metadata.head_sha)
                if full_content:
                    enclosing = _extract_scope_context(full_content, f)
            except Exception:
                enclosing = None

        if not enclosing:
            enclosing = _extract_hunk_header_context(f)

        f.enclosing_context = enclosing
        ctx.files.append(f)

        total_lines += sum(len(h.lines) for h in f.hunks)
        if total_lines > MAX_TOTAL_CONTEXT_LINES:
            ctx.truncated = True
            ctx.truncation_reason = f"Total review context size exceeded line limit ({total_lines} > {MAX_TOTAL_CONTEXT_LINES})"
            break

    ctx.total_additions = total_additions
    ctx.total_deletions = total_deletions
    return ctx


def _truncate_file_hunks(f: ChangedFile, max_lines: int) -> None:
    accumulated = 0
    truncated_hunks = []
    for hunk in f.hunks:
        if accumulated + len(hunk.lines) <= max_lines:
            truncated_hunks.append(hunk)
            accumulated += len(hunk.lines)
        else:
            remaining = max_lines - accumulated
            if remaining > 0:
                hunk.lines = hunk.lines[:remaining]
                truncated_hunks.append(hunk)
            break
    f.hunks = truncated_hunks


def _extract_hunk_header_context(f: ChangedFile) -> Optional[str]:
    """Fallback enclosing context extraction from section titles in hunk headers."""
    headers = []
    for h in f.hunks:
        if "@@" in h.header:
            parts = h.header.split("@@", 2)
            if len(parts) >= 3 and parts[2].strip():
                headers.append(parts[2].strip())
    if headers:
        return "Enclosing Sections:\n" + "\n".join(f"- {h}" for h in sorted(set(headers)))
    return None


FUNC_CLASS_REGEX = re.compile(
    r"^\s*(?:def|class|function|async def|public class|private class|func|struct|type)\s+(?P<name>[A-Za-z0-9_]+)",
    re.MULTILINE,
)
IMPORT_REGEX = re.compile(
    r"^\s*(?:import|from|require|use|include)\s+.*",
    re.MULTILINE,
)


def _extract_scope_context(full_content: str, f: ChangedFile) -> str:
    """
    Extracts top-level imports and enclosing function/class definitions for changed lines
    from the full file text at HEAD SHA.
    """
    lines = full_content.splitlines()
    changed_line_numbers = set()

    for hunk in f.hunks:
        for line in hunk.lines:
            if line.line_type == "add" and line.new_line_number:
                changed_line_numbers.add(line.new_line_number)

    # 1. Collect top-of-file imports (up to 15 lines)
    imports = []
    for idx, line in enumerate(lines[:50]):
        if IMPORT_REGEX.match(line):
            imports.append(line.strip())
            if len(imports) >= 15:
                break

    # 2. Collect enclosing function & class definitions
    scopes = []
    if changed_line_numbers:
        for lineno in sorted(changed_line_numbers):
            idx = min(lineno - 1, len(lines) - 1)
            found_func = False
            found_class = False
            while idx >= 0:
                line_str = lines[idx]
                match = FUNC_CLASS_REGEX.match(line_str)
                if match:
                    is_class = line_str.strip().startswith("class") or "class " in line_str
                    if is_class and not found_class:
                        scopes.append(f"Line {lineno} in class: `{line_str.strip()}`")
                        found_class = True
                    elif not is_class and not found_func:
                        scopes.append(f"Line {lineno} in func: `{line_str.strip()}`")
                        found_func = True
                    if found_func and found_class:
                        break
                idx -= 1

    parts = []
    if imports:
        parts.append("Imports:\n" + "\n".join(imports))
    if scopes:
        unique_scopes = sorted(set(scopes))
        parts.append("Enclosing Scopes:\n" + "\n".join(unique_scopes))

    return "\n\n".join(parts) if parts else "No enclosing scope detected"
