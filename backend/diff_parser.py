from typing import List
from backend.types import DiffChunk


def parse_unified_diff(diff_text: str) -> List[DiffChunk]:
    chunks: List[DiffChunk] = []
    current_file = None
    current_lines: list[str] = []

    lines = diff_text.splitlines()

    for line in lines:
        if line.startswith("diff --git "):
            # flush previous file
            if current_file and current_lines:
                chunks.append(
                    DiffChunk(
                        file_path=current_file,
                        patch="\n".join(current_lines),
                    )
                )
            current_file = None
            current_lines = [line]
        elif line.startswith("--- ") or line.startswith("+++ "):
            current_lines.append(line)
            if line.startswith("+++ "):
                # example: "+++ b/src/main.py"
                parts = line.split()
                if len(parts) >= 2:
                    path = parts[1]
                    # strip leading a/ or b/
                    if path.startswith("a/") or path.startswith("b/"):
                        path = path[2:]
                    current_file = path
        else:
            current_lines.append(line)

    # flush last one
    if current_file and current_lines:
        chunks.append(
            DiffChunk(
                file_path=current_file,
                patch="\n".join(current_lines),
            )
        )

    return chunks
