import ast
import json
import os
from typing import Dict, List, Optional, Tuple

_EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".mypy_cache", ".pytest_cache",
}

# Simple patterns that indicate common quality issues (plain-text heuristics)
_QUALITY_CHECKS = [
    ("bare_except", r"except\s*:", "bare except clause catches all exceptions"),
    ("print_statement", r"^\s*print\s*\(", "print() call (may be debug code)"),
    ("TODO_FIXME", r"\b(TODO|FIXME|HACK|XXX)\b", "unresolved TODO/FIXME marker"),
]

import re as _re
_QUALITY_RES = [(name, _re.compile(pat), msg) for name, pat, msg in _QUALITY_CHECKS]


def _iter_python_files(repo_path: str, target: Optional[str]) -> List[str]:
    if target:
        abs_target = target if os.path.isabs(target) else os.path.join(repo_path, target)
        if os.path.isfile(abs_target):
            rel = os.path.relpath(abs_target, repo_path).replace("\\", "/")
            return [rel] if rel.endswith(".py") else []
        if os.path.isdir(abs_target):
            root_dir = abs_target
        else:
            return []
    else:
        root_dir = repo_path

    files: List[str] = []
    for root, dirs, filenames in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in _EXCLUDE_DIRS]
        for name in filenames:
            if name.endswith(".py"):
                full = os.path.join(root, name)
                rel = os.path.relpath(full, repo_path).replace("\\", "/")
                files.append(rel)
    return files


def _check_file(repo_path: str, rel_path: str) -> Dict:
    full = os.path.join(repo_path, rel_path.replace("/", os.sep))
    errors: List[str] = []
    warnings: List[str] = []

    content = None
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with open(full, encoding=enc) as fh:
                content = fh.read()
            break
        except (UnicodeDecodeError, OSError):
            continue

    if content is None:
        return {"file": rel_path, "errors": ["unreadable"], "warnings": []}

    # Syntax check
    try:
        ast.parse(content)
    except SyntaxError as exc:
        errors.append(f"SyntaxError: {exc.msg} (line {exc.lineno})")

    # Quality checks
    for lineno, raw_line in enumerate(content.splitlines(), start=1):
        for name, pattern, msg in _QUALITY_RES:
            if pattern.search(raw_line):
                warnings.append(f"line {lineno}: [{name}] {msg}")

    return {"file": rel_path, "errors": errors, "warnings": warnings}


def run_lint_check(repo_path: str, target: Optional[str] = None) -> Tuple[int, Dict]:
    py_files = _iter_python_files(repo_path, target)
    if not py_files:
        return 0, {
            "success": True,
            "lint_mode": "syntax_and_quality",
            "files_checked": 0,
            "all_ok": True,
            "errors": [],
            "warnings": [],
            "summary": "No Python files found to check.",
        }

    results = [_check_file(repo_path, f) for f in py_files]
    all_errors: List[str] = []
    all_warnings: List[str] = []
    for r in results:
        for e in r["errors"]:
            all_errors.append(f"{r['file']}: {e}")
        for w in r["warnings"]:
            all_warnings.append(f"{r['file']}: {w}")

    all_ok = len(all_errors) == 0
    payload = {
        "success": True,
        "lint_mode": "syntax_and_quality",
        "files_checked": len(py_files),
        "all_ok": all_ok,
        "error_count": len(all_errors),
        "warning_count": len(all_warnings),
        "errors": all_errors,
        "warnings": all_warnings[:50],
        "summary": (
            f"Checked {len(py_files)} Python file(s): "
            f"{len(all_errors)} error(s), {len(all_warnings)} warning(s)."
        ),
    }
    return 0 if all_ok else 1, payload


def cmd_lint_check(repo_path: str, target: Optional[str] = None):
    code, payload = run_lint_check(repo_path, target)
    print(json.dumps(payload))
    return code, payload
