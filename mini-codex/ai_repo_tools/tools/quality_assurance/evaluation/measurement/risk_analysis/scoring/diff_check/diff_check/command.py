import ast
import json
import os
from typing import Dict, List, Optional, Set, Tuple


def _read_file_safe(path: str) -> Optional[str]:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with open(path, encoding=enc) as fh:
                return fh.read()
        except (UnicodeDecodeError, OSError):
            continue
    return None


def _extract_py_symbols(content: str) -> Tuple[Set[str], Set[str]]:
    """Return (imports_set, functions_set) from Python source."""
    imports: Set[str] = set()
    funcs: Set[str] = set()
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return imports, funcs
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.add(node.name)
        elif isinstance(node, ast.ClassDef):
            funcs.add(f"class:{node.name}")
    return imports, funcs


def _line_diff(lines_a: List[str], lines_b: List[str]) -> Tuple[int, int]:
    set_a = set(lines_a)
    set_b = set(lines_b)
    added = sum(1 for l in lines_b if l not in set_a)
    removed = sum(1 for l in lines_a if l not in set_b)
    return added, removed


def run_diff_check(repo_path: str, file_a: str, file_b: str) -> Tuple[int, Dict]:
    path_a = file_a if os.path.isabs(file_a) else os.path.join(repo_path, file_a)
    path_b = file_b if os.path.isabs(file_b) else os.path.join(repo_path, file_b)

    if not os.path.isfile(path_a):
        return 2, {"error": "file_not_found", "target": file_a}
    if not os.path.isfile(path_b):
        return 2, {"error": "file_not_found", "target": file_b}

    content_a = _read_file_safe(path_a) or ""
    content_b = _read_file_safe(path_b) or ""

    lines_a = content_a.splitlines()
    lines_b = content_b.splitlines()
    added, removed = _line_diff(lines_a, lines_b)

    is_python = file_a.endswith(".py") and file_b.endswith(".py")
    imports_changed: List[str] = []
    functions_changed: List[str] = []

    if is_python:
        imp_a, fn_a = _extract_py_symbols(content_a)
        imp_b, fn_b = _extract_py_symbols(content_b)
        imports_added = sorted(imp_b - imp_a)
        imports_removed = sorted(imp_a - imp_b)
        imports_changed = (
            [f"+{i}" for i in imports_added] + [f"-{i}" for i in imports_removed]
        )
        fns_added = sorted(fn_b - fn_a)
        fns_removed = sorted(fn_a - fn_b)
        functions_changed = (
            [f"+{f}" for f in fns_added] + [f"-{f}" for f in fns_removed]
        )

    size_delta = len(content_b) - len(content_a)
    payload = {
        "success": True,
        "file_a": file_a,
        "file_b": file_b,
        "lines_a": len(lines_a),
        "lines_b": len(lines_b),
        "lines_added": added,
        "lines_removed": removed,
        "size_delta_bytes": size_delta,
        "is_python": is_python,
        "imports_changed": imports_changed,
        "functions_changed": functions_changed,
        "summary": (
            f"{file_a} → {file_b}: "
            f"+{added}/-{removed} logical lines, "
            f"{len(functions_changed)} function/class changes, "
            f"{len(imports_changed)} import changes."
        ),
    }
    return 0, payload


def cmd_diff_check(repo_path: str, file_a: str, file_b: str):
    code, payload = run_diff_check(repo_path, file_a, file_b)
    print(json.dumps(payload))
    return code, payload
