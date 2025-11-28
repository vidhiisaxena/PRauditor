from typing import List
from backend.types import Issue


def issues_to_markdown(issues: List[Issue]) -> str:
    if not issues:
        return "✅ No issues found by the automated reviewer."

    out = ["## 🔍 Automated Code Review", ""]

    # Group by kind
    groups: dict[str, List[Issue]] = {}
    for issue in issues:
        groups.setdefault(issue.kind, []).append(issue)

    for kind, items in groups.items():
        out.append(f"### {kind.capitalize()} issues ({len(items)})")
        out.append("")
        out.append("| File | Line | Severity | Message |")
        out.append("|------|------|----------|---------|")

        for it in items:
            msg = it.message.replace("\n", " ")
            out.append(
                f"| `{it.file_path}` | {it.line or '-'} | {it.severity} | {msg} |"
            )

        out.append("")

    return "\n".join(out)
