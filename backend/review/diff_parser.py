import re
from typing import List, Optional

from backend.review.types import DiffChunk, ChangedFile, DiffHunk, ChangedLine


def parse_unified_diff(diff_text: str) -> List[DiffChunk]:
    """
    Legacy diff parser entry point for backward compatibility.
    Converts raw unified diff string into a list of legacy DiffChunk objects.
    """
    files = parse_unified_diff_extended(diff_text)
    chunks: List[DiffChunk] = []

    for f in files:
        if f.is_binary or not f.hunks:
            continue
        patch_lines = []
        for h in f.hunks:
            patch_lines.append(h.header)
            for line in h.lines:
                if line.line_type == "add":
                    prefix = "+"
                elif line.line_type == "delete":
                    prefix = "-"
                else:
                    prefix = " "
                patch_lines.append(f"{prefix}{line.content}")
        patch_text = "\n".join(patch_lines)
        chunks.append(DiffChunk(file_path=f.path, patch=patch_text))

    return chunks


def parse_unified_diff_extended(diff_text: str) -> List[ChangedFile]:
    """
    Extended unified diff parser.
    Parses unified diff into structured ChangedFile objects with line-by-line number tracking.
    """
    if not diff_text or not diff_text.strip():
        return []

    file_blocks = _split_into_file_diffs(diff_text)
    changed_files: List[ChangedFile] = []

    for block in file_blocks:
        parsed_file = _parse_single_file_diff(block)
        if parsed_file:
            changed_files.append(parsed_file)

    return changed_files


def _split_into_file_diffs(diff_text: str) -> List[str]:
    """Splits full diff text into per-file diff blocks."""
    blocks: List[str] = []
    current_block: List[str] = []

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            if current_block:
                blocks.append("\n".join(current_block))
            current_block = [line]
        else:
            current_block.append(line)

    if current_block:
        blocks.append("\n".join(current_block))

    return blocks


HUNK_HEADER_REGEX = re.compile(
    r"^@@\s+-(?P<old_start>\d+)(?:,(?P<old_count>\d+))?\s+\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))?\s+@@(?P<section>\s+.*)?$"
)


def _parse_single_file_diff(block_text: str) -> Optional[ChangedFile]:
    lines = block_text.splitlines()
    if not lines:
        return None

    path = None
    old_path = None
    status = "modified"
    is_binary = False

    # Inspect header lines for path, status, and binary markers
    for line in lines:
        if line.startswith("rename from "):
            old_path = line[len("rename from ") :].strip()
            status = "renamed"
        elif line.startswith("rename to "):
            path = line[len("rename to ") :].strip()
            status = "renamed"
        elif line.startswith("new file mode "):
            status = "added"
        elif line.startswith("deleted file mode "):
            status = "deleted"
        elif line.startswith("Binary files ") or "GIT binary patch" in line or line.startswith("Binary file "):
            is_binary = True
            status = "binary"
        elif line.startswith("--- "):
            raw_old = line[4:].strip()
            if raw_old != "/dev/null":
                if raw_old.startswith("a/") or raw_old.startswith("b/"):
                    old_path = raw_old[2:]
                else:
                    old_path = raw_old
        elif line.startswith("+++ "):
            raw_new = line[4:].strip()
            if raw_new != "/dev/null":
                if raw_new.startswith("a/") or raw_new.startswith("b/"):
                    path = raw_new[2:]
                else:
                    path = raw_new

    # Fallback path parsing from `diff --git a/path b/path` if +++ is absent or /dev/null
    if not path:
        first_line = lines[0]
        if first_line.startswith("diff --git "):
            parts = first_line.split()
            if len(parts) >= 4:
                b_part = parts[3]
                a_part = parts[2]
                if b_part.startswith("b/"):
                    path = b_part[2:]
                else:
                    path = b_part
                if a_part.startswith("a/"):
                    old_path = a_part[2:]
                else:
                    old_path = a_part

    if not path and not old_path:
        return None

    final_path = path or old_path or "unknown"
    changed_file = ChangedFile(
        path=final_path,
        old_path=old_path if (old_path and old_path != final_path) else None,
        status=status,
        is_binary=is_binary,
    )

    if is_binary:
        return changed_file

    # Parse Hunks and line numbers
    current_hunk: Optional[DiffHunk] = None
    old_lineno = 0
    new_lineno = 0

    for line in lines:
        match = HUNK_HEADER_REGEX.match(line)
        if match:
            if current_hunk:
                changed_file.hunks.append(current_hunk)

            old_start = int(match.group("old_start"))
            old_count = int(match.group("old_count")) if match.group("old_count") is not None else 1
            new_start = int(match.group("new_start"))
            new_count = int(match.group("new_count")) if match.group("new_count") is not None else 1

            current_hunk = DiffHunk(
                old_start=old_start,
                old_lines=old_count,
                new_start=new_start,
                new_lines=new_count,
                header=line,
            )
            old_lineno = old_start
            new_lineno = new_start
            continue

        if current_hunk is None:
            continue  # Header lines before the first hunk

        if line.startswith("+"):
            content = line[1:]
            changed_file.additions += 1
            current_hunk.lines.append(
                ChangedLine(
                    file_path=final_path,
                    old_line_number=None,
                    new_line_number=new_lineno,
                    line_type="add",
                    content=content,
                )
            )
            new_lineno += 1
        elif line.startswith("-"):
            content = line[1:]
            changed_file.deletions += 1
            current_hunk.lines.append(
                ChangedLine(
                    file_path=final_path,
                    old_line_number=old_lineno,
                    new_line_number=None,
                    line_type="delete",
                    content=content,
                )
            )
            old_lineno += 1
        elif line.startswith(" ") or line == "":
            content = line[1:] if line.startswith(" ") else line
            current_hunk.lines.append(
                ChangedLine(
                    file_path=final_path,
                    old_line_number=old_lineno,
                    new_line_number=new_lineno,
                    line_type="context",
                    content=content,
                )
            )
            old_lineno += 1
            new_lineno += 1
        elif line.startswith("\\ No newline at end of file"):
            continue

    if current_hunk:
        changed_file.hunks.append(current_hunk)

    return changed_file
