from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class DiffChunk:
    file_path: str
    patch: str


@dataclass
class Issue:
    file_path: str
    line: Optional[int]
    kind: str        # "logic" | "readability" | "performance" | "security" | "redundancy"
    severity: str    # "info" | "minor" | "major" | "critical"
    message: str
    suggestion: Optional[str]


@dataclass
class ChangedLine:
    file_path: str
    old_line_number: Optional[int]
    new_line_number: Optional[int]
    line_type: str  # "add" | "delete" | "context"
    content: str


@dataclass
class DiffHunk:
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    header: str
    lines: List[ChangedLine] = field(default_factory=list)


@dataclass
class ChangedFile:
    path: str
    old_path: Optional[str] = None
    status: str = "modified"  # "modified" | "added" | "deleted" | "renamed" | "binary"
    is_binary: bool = False
    is_ignored: bool = False
    additions: int = 0
    deletions: int = 0
    hunks: List[DiffHunk] = field(default_factory=list)
    enclosing_context: Optional[str] = None


@dataclass
class PRMetadata:
    title: str = ""
    description: str = ""
    repo_full_name: str = ""
    pr_number: int = 0
    base_sha: str = ""
    head_sha: str = ""


@dataclass
class ReviewContext:
    metadata: PRMetadata
    files: List[ChangedFile] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0
    truncated: bool = False
    truncation_reason: Optional[str] = None
