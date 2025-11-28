from dataclasses import dataclass
from typing import Optional, List


@dataclass
class DiffChunk:
    file_path: str
    patch: str  


@dataclass
class Issue:
    file_path: str
    line: Optional[int]
    kind: str        # "logic" | "readability" | "performance" | "security"
    severity: str    # "info" | "minor" | "major" | "critical"
    message: str
    suggestion: Optional[str]
