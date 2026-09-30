"""
Deterministic static pattern analyzers for PRauditor.

Analyzes changed/added code only using AST (Python) and regex patterns.
Fast (<100ms), deterministic, zero LLM cost.
"""

from dataclasses import dataclass
from typing import List, Optional, Set, Dict, Any, Tuple
import ast
import re
import logging

from backend.review.types import ChangedFile, DiffHunk, ChangedLine

logger = logging.getLogger(__name__)


@dataclass
class StaticFinding:
    detector: str        # "sql_injection", "n_plus_one", etc.
    file_path: str
    line: int
    category: str        # "security", "performance", "correctness", "maintainability"
    severity: str        # "critical", "major", "minor", "suggestion"
    title: str           # short title
    message: str         # explanation
    evidence: str        # the exact code that triggered detection
    confidence: float    # 0.0-1.0 (deterministic detectors: 0.90-1.0)
    is_optional: bool
    suggestion: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers for AST extraction and line mapping
# ---------------------------------------------------------------------------

def _get_added_lines_map(file: ChangedFile) -> Tuple[Set[int], Dict[int, str]]:
    """Return set of added line numbers and map of line_number -> line_content."""
    added_numbers: Set[int] = set()
    line_contents: Dict[int, str] = {}
    for hunk in file.hunks:
        for line in hunk.lines:
            if line.line_type == "add" and line.new_line_number is not None:
                added_numbers.add(line.new_line_number)
                line_contents[line.new_line_number] = line.content
            elif line.new_line_number is not None:
                line_contents[line.new_line_number] = line.content
    return added_numbers, line_contents


def _parse_hunk_ast(
    hunk: DiffHunk,
) -> Tuple[Optional[ast.AST], Dict[int, int]]:
    """
    Parse a diff hunk into an AST tree and return (ast_tree, line_map).
    line_map maps AST node lineno -> actual new_line_number in the file.
    Tries full hunk first, then added lines only if context lines cause indentation conflicts.
    """
    candidates = []
    # Candidate 1: full hunk (context + add)
    full_lines = [
        (line.new_line_number, line.content)
        for line in hunk.lines
        if line.line_type in ("add", "context") and line.new_line_number is not None
    ]
    if full_lines:
        candidates.append(full_lines)

    # Candidate 2: added lines only
    add_only = [
        (line.new_line_number, line.content)
        for line in hunk.lines
        if line.line_type == "add" and line.new_line_number is not None
    ]
    if add_only:
        candidates.append(add_only)

    for lines in candidates:
        # Attempt 1: Direct padded parse so node.lineno directly equals new_line_number
        max_line = lines[-1][0]
        padded = [""] * max_line
        for ln, content in lines:
            padded[ln - 1] = content
        try:
            tree = ast.parse("\n".join(padded))
            return tree, {i: i for i in range(1, max_line + 1)}
        except Exception:
            pass

        # Attempt 2: Dedented lines with index mapping
        non_empty = [c for _, c in lines if c.strip()]
        min_indent = min((len(c) - len(c.lstrip()) for c in non_empty), default=0)
        dedented_lines = [
            (num, c[min_indent:] if len(c) >= min_indent else c)
            for num, c in lines
        ]
        line_map = {idx + 1: num for idx, (num, _) in enumerate(dedented_lines)}
        dedented_text = "\n".join(c for _, c in dedented_lines)

        try:
            tree = ast.parse(dedented_text)
            return tree, line_map
        except Exception:
            pass

        # Attempt 3: Wrapped in synthetic function (for returns, yields, indented blocks)
        wrapped = "def _synthetic_wrap():\n" + "\n".join("    " + c for _, c in dedented_lines)
        wrapped_map = {idx + 2: num for idx, (num, _) in enumerate(dedented_lines)}
        try:
            tree = ast.parse(wrapped)
            return tree, wrapped_map
        except Exception:
            pass

        # Attempt 4: Wrapped in async function (for awaits)
        wrapped_async = "async def _synthetic_wrap():\n" + "\n".join("    " + c for _, c in dedented_lines)
        try:
            tree = ast.parse(wrapped_async)
            return tree, wrapped_map
        except Exception:
            pass

    return None, {}


# ---------------------------------------------------------------------------
# Python AST Detectors
# ---------------------------------------------------------------------------

SQL_KEYWORDS = re.compile(
    r"\b(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|DROP\s+TABLE|ALTER\s+TABLE|CREATE\s+TABLE)\b",
    re.IGNORECASE,
)
SQL_METHOD_NAMES = {"execute", "raw", "cursor", "text", "query"}


def _detect_sql_injection(
    tree: ast.AST,
    line_map: Dict[int, int],
    added_lines: Set[int],
    line_contents: Dict[int, str],
    file_path: str,
) -> List[StaticFinding]:
    """Detector 1: SQL injection via f-strings, .format(), + or % inside SQL calls/queries."""
    findings: List[StaticFinding] = []

    def _is_suspicious_query_expr(node: ast.AST) -> Tuple[bool, str]:
        # f-string: JoinedStr
        if isinstance(node, ast.JoinedStr):
            return True, "f-string formatting in SQL query"
        # .format() call
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "format":
                return True, ".format() method in SQL query"
        # String concatenation or % formatting
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, (ast.Add, ast.Mod)):
                return True, "string concatenation or % operator in SQL query"
        return False, ""

    for node in ast.walk(tree):
        real_line = line_map.get(getattr(node, "lineno", -1))
        if not real_line or real_line not in added_lines:
            continue

        # Pattern A: db.execute(f"SELECT...", ...) or cursor.execute("SELECT {}".format(...))
        if isinstance(node, ast.Call):
            attr_name = ""
            if isinstance(node.func, ast.Attribute):
                attr_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                attr_name = node.func.id

            if attr_name in SQL_METHOD_NAMES and node.args:
                first_arg = node.args[0]
                is_sus, desc = _is_suspicious_query_expr(first_arg)
                if is_sus:
                    evidence = line_contents.get(real_line, "").strip()
                    findings.append(
                        StaticFinding(
                            detector="sql_injection",
                            file_path=file_path,
                            line=real_line,
                            category="security",
                            severity="critical",
                            title="SQL injection vulnerability",
                            message=f"SQL query dynamically constructed using {desc}.",
                            evidence=evidence,
                            confidence=0.95,
                            is_optional=False,
                            suggestion="Use parameterized queries with placeholder bindings instead of string interpolation.",
                        )
                    )

        # Pattern B: query = f"SELECT ... WHERE ..."
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            val = node.value if isinstance(node, ast.Assign) else node.value
            if val is not None:
                is_sus, desc = _is_suspicious_query_expr(val)
                if is_sus:
                    evidence = line_contents.get(real_line, "").strip()
                    if SQL_KEYWORDS.search(evidence):
                        findings.append(
                            StaticFinding(
                                detector="sql_injection",
                                file_path=file_path,
                                line=real_line,
                                category="security",
                                severity="critical",
                                title="SQL injection vulnerability",
                                message=f"SQL statement constructed using {desc}.",
                                evidence=evidence,
                                confidence=0.95,
                                is_optional=False,
                                suggestion="Use parameterized queries instead of formatting raw SQL strings.",
                            )
                        )

    return findings


DB_CALL_NAMES = {
    "execute", "query", "fetchall", "fetchone", "fetchmany",
    "select", "filter", "all", "first", "insert", "delete", "update",
}
NETWORK_MODULES = {"requests", "httpx", "aiohttp", "urllib"}


def _detect_calls_in_loops(
    tree: ast.AST,
    line_map: Dict[int, int],
    added_lines: Set[int],
    line_contents: Dict[int, str],
    file_path: str,
) -> List[StaticFinding]:
    """Detector 2: Database or network call inside for/while loops (N+1 issue)."""
    findings: List[StaticFinding] = []
    seen_lines: Set[int] = set()

    def _check_loop_body(body_nodes: List[ast.AST]):
        for stmt in body_nodes:
            for child in ast.walk(stmt):
                # Don't recurse into nested function definitions
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue

                if isinstance(child, ast.Call):
                    real_line = line_map.get(getattr(child, "lineno", -1))
                    if not real_line or real_line not in added_lines or real_line in seen_lines:
                        continue

                    is_db = False
                    is_net = False
                    evidence = line_contents.get(real_line, "").strip()

                    # Check db call
                    if isinstance(child.func, ast.Attribute):
                        if child.func.attr in DB_CALL_NAMES:
                            is_db = True
                        if isinstance(child.func.value, ast.Name) and child.func.value.id in NETWORK_MODULES:
                            is_net = True
                    elif isinstance(child.func, ast.Name):
                        if child.func.id in ("fetch", "execute", "query"):
                            is_db = True

                    if is_db or is_net:
                        seen_lines.add(real_line)
                        op_type = "Database" if is_db else "Network"
                        findings.append(
                            StaticFinding(
                                detector="call_inside_loop",
                                file_path=file_path,
                                line=real_line,
                                category="performance",
                                severity="major",
                                title=f"{op_type} call inside loop (N+1 query pattern)",
                                message=f"Repeatedly executing {op_type.lower()} calls inside a loop creates performance bottlenecks.",
                                evidence=evidence,
                                confidence=0.92,
                                is_optional=False,
                                suggestion="Fetch required data in batch prior to the loop (e.g., using WHERE id IN (...) or bulk APIs).",
                            )
                        )

    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            _check_loop_body(node.body)

    return findings


BLOCKING_CALLS = {
    ("time", "sleep"),
    ("requests", "get"),
    ("requests", "post"),
    ("requests", "put"),
    ("requests", "delete"),
    ("requests", "request"),
    ("os", "system"),
    ("subprocess", "run"),
    ("subprocess", "call"),
    ("subprocess", "Popen"),
    ("subprocess", "check_output"),
}


def _detect_blocking_in_async(
    tree: ast.AST,
    line_map: Dict[int, int],
    added_lines: Set[int],
    line_contents: Dict[int, str],
    file_path: str,
) -> List[StaticFinding]:
    """Detector 3: Blocking calls inside async functions."""
    findings: List[StaticFinding] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    real_line = line_map.get(getattr(child, "lineno", -1))
                    if not real_line or real_line not in added_lines:
                        continue

                    is_blocking = False
                    call_name = ""

                    if isinstance(child.func, ast.Attribute) and isinstance(child.func.value, ast.Name):
                        mod = child.func.value.id
                        func = child.func.attr
                        if (mod, func) in BLOCKING_CALLS:
                            is_blocking = True
                            call_name = f"{mod}.{func}"
                    elif isinstance(child.func, ast.Name):
                        if child.func.id == "open":
                            is_blocking = True
                            call_name = "open"

                    if is_blocking:
                        evidence = line_contents.get(real_line, "").strip()
                        findings.append(
                            StaticFinding(
                                detector="blocking_call_in_async",
                                file_path=file_path,
                                line=real_line,
                                category="performance",
                                severity="major",
                                title="Blocking call in async function",
                                message=f"Synchronous blocking call '{call_name}()' blocks the async event loop.",
                                evidence=evidence,
                                confidence=0.90,
                                is_optional=False,
                                suggestion="Use non-blocking async alternatives (e.g. asyncio.sleep, httpx, aiofiles) or run in an executor thread.",
                            )
                        )

    return findings


def _detect_bare_except(
    tree: ast.AST,
    line_map: Dict[int, int],
    added_lines: Set[int],
    line_contents: Dict[int, str],
    file_path: str,
) -> List[StaticFinding]:
    """Detector 4: Bare except or except Exception clause."""
    findings: List[StaticFinding] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            real_line = line_map.get(getattr(node, "lineno", -1))
            if not real_line or real_line not in added_lines:
                continue

            is_bare = False
            message = ""
            if node.type is None:
                is_bare = True
                message = "Bare 'except:' catches all exceptions including system-exiting signals."
            elif isinstance(node.type, ast.Name) and node.type.id in ("Exception", "BaseException"):
                is_bare = True
                message = f"Catching broad '{node.type.id}' obscures unintended bugs and error handling."

            if is_bare:
                evidence = line_contents.get(real_line, "").strip()
                findings.append(
                    StaticFinding(
                        detector="bare_except",
                        file_path=file_path,
                        line=real_line,
                        category="correctness",
                        severity="major",
                        title="Bare or overly broad except clause",
                        message=message,
                        evidence=evidence,
                        confidence=0.95,
                        is_optional=False,
                        suggestion="Catch specific exception types (e.g. except (ValueError, KeyError):).",
                    )
                )

    return findings


def _detect_mutable_default(
    tree: ast.AST,
    line_map: Dict[int, int],
    added_lines: Set[int],
    line_contents: Dict[int, str],
    file_path: str,
) -> List[StaticFinding]:
    """Detector 5: Mutable default arguments in functions."""
    findings: List[StaticFinding] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_line = line_map.get(getattr(node, "lineno", -1))
            defaults = node.args.defaults + [d for d in node.args.kw_defaults if d is not None]

            for default in defaults:
                is_mutable = False
                val_repr = ""

                if isinstance(default, ast.List):
                    is_mutable = True
                    val_repr = "[]"
                elif isinstance(default, ast.Dict):
                    is_mutable = True
                    val_repr = "{}"
                elif isinstance(default, ast.Set):
                    is_mutable = True
                    val_repr = "set()"
                elif isinstance(default, ast.Call) and isinstance(default.func, ast.Name) and default.func.id in ("list", "dict", "set"):
                    is_mutable = True
                    val_repr = f"{default.func.id}()"

                if is_mutable:
                    arg_line = line_map.get(getattr(default, "lineno", -1)) or func_line
                    # Flag if either default arg line or function def line was added
                    if (arg_line and arg_line in added_lines) or (func_line and func_line in added_lines):
                        target_line = arg_line or func_line
                        evidence = line_contents.get(target_line, "").strip()
                        findings.append(
                            StaticFinding(
                                detector="mutable_default_argument",
                                file_path=file_path,
                                line=target_line,
                                category="correctness",
                                severity="major",
                                title="Mutable default argument",
                                message=f"Default argument is mutable ({val_repr}) and will retain state across calls.",
                                evidence=evidence,
                                confidence=0.95,
                                is_optional=False,
                                suggestion="Use None as default and initialize within function body (e.g. if arg is None: arg = []).",
                            )
                        )

    return findings


SECRET_NAME_PATTERNS = re.compile(
    r"(secret|password|passwd|token|api_?key|private_?key)",
    re.IGNORECASE,
)
SAFE_SECRET_VALUES = {
    "", "placeholder", "dummy", "your_key_here", "changeme", "test", "fake", "none", "null"
}


def _detect_hardcoded_secrets_ast(
    tree: ast.AST,
    line_map: Dict[int, int],
    added_lines: Set[int],
    line_contents: Dict[int, str],
    file_path: str,
) -> List[StaticFinding]:
    """Detector 6: Hardcoded secrets in variable assignments."""
    findings: List[StaticFinding] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            real_line = line_map.get(getattr(node, "lineno", -1))
            if not real_line or real_line not in added_lines:
                continue

            target_names = []
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        target_names.append(t.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                target_names.append(node.target.id)

            val_node = node.value if isinstance(node, ast.Assign) else node.value
            if val_node is None or not isinstance(val_node, ast.Constant):
                # If it's a Call (e.g. os.getenv), it is NOT an ast.Constant, so it is safe!
                continue

            val = str(val_node.value).strip()
            if not val or len(val) < 4 or val.lower() in SAFE_SECRET_VALUES:
                continue

            for name in target_names:
                if SECRET_NAME_PATTERNS.search(name):
                    evidence = line_contents.get(real_line, "").strip()
                    findings.append(
                        StaticFinding(
                            detector="hardcoded_secret",
                            file_path=file_path,
                            line=real_line,
                            category="security",
                            severity="critical",
                            title="Hardcoded secret or credential",
                            message=f"Variable '{name}' appears to contain a hardcoded credential literal.",
                            evidence=evidence,
                            confidence=0.95,
                            is_optional=False,
                            suggestion="Store secrets in environment variables (e.g. os.getenv(...)) or a secure secret store.",
                        )
                    )
                    break

    return findings


# ---------------------------------------------------------------------------
# Language-Agnostic Regex Detectors (Added Lines Only)
# ---------------------------------------------------------------------------

RE_CREDENTIALS = re.compile(
    r"""(?i)\b(?:password|passwd|api[_-]?key|secret[_-]?key|private[_-]?key|auth[_-]?token)\s*[:=]\s*["']([^"'\s]{6,})["']|Authorization:\s*Bearer\s+([A-Za-z0-9\-._~+/]{8,})"""
)
RE_DEBUG_STMTS = re.compile(
    r"""\b(?:console\.(?:log|debug|warn|error|trace)|print|debugger|binding\.pry|dd|var_dump)\s*(?:\(|\b)"""
)
RE_TODO_FIXME = re.compile(
    r"""\b(TODO|FIXME|HACK|XXX)\b\s*[:\-]?(.*)"""
)
RE_SUSPICIOUS = re.compile(
    r"""(?:\b(?:eval|exec|__import__)\s*\(|subprocess\.(?:call|run|Popen)\s*\(.*shell\s*=\s*True)"""
)

TEST_FILE_PATH_RE = re.compile(
    r"""(?:^|[/\\])(?:tests?|specs?|__tests__|testing)[/\\]|(?:test_|spec_|_test\.|_spec\.)""",
    re.IGNORECASE,
)


def _detect_regex_patterns(
    file: ChangedFile,
    added_lines: Set[int],
    line_contents: Dict[int, str],
) -> List[StaticFinding]:
    """Run regex-based detectors on added lines."""
    findings: List[StaticFinding] = []
    is_test_file = bool(TEST_FILE_PATH_RE.search(file.path))

    for line_num in sorted(added_lines):
        line = line_contents.get(line_num, "")
        stripped = line.strip()
        if not stripped:
            continue

        # Detector 7: Hardcoded credentials regex
        # Skip if file is documentation or env example
        if not (file.path.endswith(".example") or file.path.endswith(".md")):
            m_cred = RE_CREDENTIALS.search(stripped)
            if m_cred:
                # Ignore if using environment variable retrieval or string placeholder
                if not re.search(r"(?:getenv|environ|process\.env|\$\{)", stripped, re.IGNORECASE):
                    findings.append(
                        StaticFinding(
                            detector="hardcoded_credentials_regex",
                            file_path=file.path,
                            line=line_num,
                            category="security",
                            severity="critical",
                            title="Hardcoded credential pattern",
                            message="Potential hardcoded credential or bearer token detected in changed line.",
                            evidence=stripped,
                            confidence=0.92,
                            is_optional=False,
                            suggestion="Load sensitive credentials via environment variables.",
                        )
                    )

        # Detector 8: Debug statements in non-test code
        if not is_test_file:
            if RE_DEBUG_STMTS.search(stripped):
                findings.append(
                    StaticFinding(
                        detector="debug_statements",
                        file_path=file.path,
                        line=line_num,
                        category="maintainability",
                        severity="minor",
                        title="Debug statement left in code",
                        message="Console log or debug statement left in non-test source code.",
                        evidence=stripped,
                        confidence=0.90,
                        is_optional=False,
                        suggestion="Remove debug statement or replace with standard application logging.",
                    )
                )

        # Detector 9: TODO / FIXME / HACK
        m_todo = RE_TODO_FIXME.search(stripped)
        if m_todo:
            findings.append(
                StaticFinding(
                    detector="todo_comment",
                    file_path=file.path,
                    line=line_num,
                    category="maintainability",
                    severity="suggestion",
                    title="TODO / temporary marker in new code",
                    message=f"Temporary marker ({m_todo.group(1)}) detected in added code.",
                    evidence=stripped,
                    confidence=0.95,
                    is_optional=True,
                    suggestion="Verify if this task should be completed prior to merge or tracked in an issue.",
                )
            )

        # Detector 10: Suspicious dynamic execution patterns
        if RE_SUSPICIOUS.search(stripped):
            findings.append(
                StaticFinding(
                    detector="suspicious_patterns",
                    file_path=file.path,
                    line=line_num,
                    category="security",
                    severity="critical",
                    title="Suspicious dynamic execution pattern",
                    message="Use of eval, exec, __import__, or shell=True detected.",
                    evidence=stripped,
                    confidence=0.95,
                    is_optional=False,
                    suggestion="Avoid dynamic execution functions; use safe and structured APIs instead.",
                )
            )

    return findings


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def run_static_analysis(changed_files: List[ChangedFile]) -> List[StaticFinding]:
    """
    Runs ALL deterministic detectors against changed files and returns combined findings.
    Each detector is isolated in try/except so one failure cannot crash others.
    """
    all_findings: List[StaticFinding] = []

    for file in changed_files:
        if file.is_binary or file.is_ignored or not file.hunks:
            continue

        added_lines, line_contents = _get_added_lines_map(file)
        if not added_lines:
            continue

        # 1. AST Analyzers for Python files
        if file.path.endswith(".py"):
            for hunk in file.hunks:
                try:
                    tree, line_map = _parse_hunk_ast(hunk)
                    if not tree:
                        continue

                    # Run each AST detector independently
                    ast_detectors = [
                        _detect_sql_injection,
                        _detect_calls_in_loops,
                        _detect_blocking_in_async,
                        _detect_bare_except,
                        _detect_mutable_default,
                        _detect_hardcoded_secrets_ast,
                    ]

                    for detector_fn in ast_detectors:
                        try:
                            results = detector_fn(tree, line_map, added_lines, line_contents, file.path)
                            all_findings.extend(results)
                        except Exception as det_err:
                            logger.warning(
                                f"[StaticAnalysis] Detector {detector_fn.__name__} failed on {file.path}: {det_err}"
                            )
                except Exception as parse_err:
                    # Silently skip if AST parsing cannot complete
                    logger.debug(f"[StaticAnalysis] Skipping AST on hunk in {file.path}: {parse_err}")

        # 2. Regex Analyzers (Language-agnostic)
        try:
            regex_results = _detect_regex_patterns(file, added_lines, line_contents)
            all_findings.extend(regex_results)
        except Exception as reg_err:
            logger.warning(f"[StaticAnalysis] Regex detector failed on {file.path}: {reg_err}")

    # Deduplicate findings on (file_path, line, detector or category)
    seen: Set[Tuple[str, int, str]] = set()
    deduped: List[StaticFinding] = []
    for f in all_findings:
        key = (f.file_path, f.line, f.detector)
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    return deduped
