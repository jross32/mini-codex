import json
import os
import re
from typing import Dict, List, Optional, Tuple

_EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".mypy_cache", ".pytest_cache",
}

_BINARY_EXTENSIONS = {
    ".pyc", ".pyo", ".so", ".dll", ".pyd", ".exe", ".bin",
    ".jpg", ".jpeg", ".png", ".gif", ".ico", ".svg",
    ".zip", ".tar", ".gz", ".whl",
    ".db", ".sqlite", ".sqlite3",
}


def _is_binary_path(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in _BINARY_EXTENSIONS


def _iter_repo_files(repo_path: str, path_filter: Optional[str]) -> List[str]:
    results: List[str] = []
    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in _EXCLUDE_DIRS]
        for name in filenames:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, repo_path).replace("\\", "/")
            if _is_binary_path(rel):
                continue
            if path_filter and not fnmatch_simple(rel, path_filter):
                continue
            results.append(rel)
    return results


def fnmatch_simple(path: str, pattern: str) -> bool:
    """Minimal glob-style filter: supports * wildcard and substring match."""
    if "*" in pattern:
        regex = re.escape(pattern).replace(r"\*", ".*")
        return bool(re.search(regex, path, re.IGNORECASE))
    return pattern.lower() in path.lower()


def run_code_search(
    repo_path: str,
    pattern: str,
    path_filter: Optional[str] = None,
    max_results: int = 50,
) -> Tuple[int, Dict]:
    if not pattern:
        return 2, {"error": "missing_argument", "detail": "pattern is required"}

    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        return 2, {"error": "invalid_pattern", "detail": str(exc)}

    rel_files = _iter_repo_files(repo_path, path_filter)
    matches: List[Dict] = []
    files_searched = 0
    truncated = False

    for rel in rel_files:
        if len(matches) >= max_results:
            truncated = True
            break
        full = os.path.join(repo_path, rel.replace("/", os.sep))
        try:
            for enc in ("utf-8", "utf-8-sig", "latin-1"):
                try:
                    with open(full, encoding=enc) as fh:
                        lines = fh.readlines()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                continue
        except OSError:
            continue

        files_searched += 1
        for lineno, line in enumerate(lines, start=1):
            m = compiled.search(line)
            if m:
                matches.append({
                    "file": rel,
                    "line": lineno,
                    "text": line.rstrip("\n"),
                    "match_start": m.start(),
                    "match_end": m.end(),
                })
                if len(matches) >= max_results:
                    truncated = True
                    break

    payload = {
        "success": True,
        "pattern": pattern,
        "path_filter": path_filter,
        "files_searched": files_searched,
        "match_count": len(matches),
        "truncated": truncated,
        "max_results": max_results,
        "matches": matches,
        "summary": (
            f"Found {len(matches)} match(es) for '{pattern}' "
            f"across {files_searched} file(s)"
            + (" (results truncated)" if truncated else "") + "."
        ),
    }
    return 0, payload


def cmd_code_search(
    repo_path: str,
    pattern: str,
    path_filter: Optional[str] = None,
    max_results: int = 50,
):
    code, payload = run_code_search(repo_path, pattern, path_filter, max_results)
    print(json.dumps(payload))
    return code, payload
