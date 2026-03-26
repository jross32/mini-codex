import json
import os
import re
from typing import Dict, List, Optional, Tuple

_ERROR_RE = re.compile(r"\b(error|exception|traceback|critical)\b", re.IGNORECASE)
_WARNING_RE = re.compile(r"\b(warn|warning)\b", re.IGNORECASE)
_TOOL_RE = re.compile(r"\[tool\]\s+(\w+)", re.IGNORECASE)


def _find_log(repo_path: str, log_path: str) -> Optional[str]:
    if os.path.isabs(log_path):
        return log_path if os.path.isfile(log_path) else None
    abs_path = os.path.join(repo_path, log_path)
    return abs_path if os.path.isfile(abs_path) else None


def _read_tail(path: str, n: int) -> List[str]:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with open(path, encoding=enc) as fh:
                lines = fh.readlines()
            return lines[-n:] if len(lines) > n else lines
        except (UnicodeDecodeError, OSError):
            continue
    return []


def run_log_tail(repo_path: str, log_path: str, lines: int = 50) -> Tuple[int, Dict]:
    if not log_path:
        return 2, {"error": "missing_argument", "detail": "log_path is required"}

    lines = max(1, min(lines, 2000))
    resolved = _find_log(repo_path, log_path)
    if not resolved:
        return 2, {"error": "file_not_found", "target": log_path}

    tail = _read_tail(resolved, lines)
    error_count = sum(1 for l in tail if _ERROR_RE.search(l))
    warning_count = sum(1 for l in tail if _WARNING_RE.search(l))

    last_tool = None
    for line in reversed(tail):
        m = _TOOL_RE.search(line)
        if m:
            last_tool = m.group(1)
            break

    # Try to parse JSONL and extract last tool from structured logs
    if last_tool is None:
        for line in reversed(tail):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
                if isinstance(obj, dict) and "tool" in obj:
                    last_tool = obj["tool"]
                    break
            except json.JSONDecodeError:
                pass

    payload = {
        "success": True,
        "log_path": log_path,
        "lines_requested": lines,
        "lines_returned": len(tail),
        "error_count": error_count,
        "warning_count": warning_count,
        "last_tool_used": last_tool,
        "tail_lines": [l.rstrip("\n") for l in tail],
        "summary": (
            f"Tail of {os.path.basename(resolved)} "
            f"({len(tail)} lines): "
            f"{error_count} error(s), {warning_count} warning(s); "
            f"last tool: {last_tool or 'unknown'}."
        ),
    }
    return 0, payload


def cmd_log_tail(repo_path: str, log_path: str, lines: int = 50):
    code, payload = run_log_tail(repo_path, log_path, lines)
    print(json.dumps(payload))
    return code, payload
