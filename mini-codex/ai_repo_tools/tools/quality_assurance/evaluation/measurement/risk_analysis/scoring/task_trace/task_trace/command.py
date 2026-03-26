import json
import os
import re
from typing import Dict, List, Optional, Tuple

# Patterns to recognise log lines emitted by agent_loop / tool_runner
_TOOL_CALL_RE = re.compile(r"\[tool\]\s+(\w+)", re.IGNORECASE)
_STEP_RE = re.compile(r"step\s+(\d+)", re.IGNORECASE)
_STATUS_RE = re.compile(r"\b(ok|success|fail|error|done|complete|skip)\b", re.IGNORECASE)
_FALLBACK_RE = re.compile(r"fallback", re.IGNORECASE)
_AISH_RE = re.compile(r"aish", re.IGNORECASE)


def _default_log_path(repo_path: str) -> Optional[str]:
    """Find the most recent .log or .jsonl in agent_logs/."""
    for candidate in ("agent_logs", "mini-codex/agent_logs"):
        folder = os.path.join(repo_path, candidate)
        if not os.path.isdir(folder):
            continue
        logs = [
            f for f in os.listdir(folder)
            if f.endswith((".log", ".jsonl", ".json"))
        ]
        if logs:
            logs.sort()
            return os.path.join(folder, logs[-1])
    return None


def _read_lines(path: str) -> List[str]:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with open(path, encoding=enc) as fh:
                return fh.readlines()
        except (UnicodeDecodeError, OSError):
            continue
    return []


def _parse_jsonl_steps(lines: List[str]) -> List[Dict]:
    """Try to parse JSONL-format agent logs."""
    steps = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict) and "tool" in obj:
                steps.append({
                    "tool": obj.get("tool", "unknown"),
                    "args": obj.get("args", []),
                    "outcome": obj.get("outcome", obj.get("status", "unknown")),
                    "used_aish_auto": obj.get("used_aish_auto", False),
                    "duration_ms": obj.get("duration_ms"),
                })
        except json.JSONDecodeError:
            pass
    return steps


def _parse_plain_steps(lines: List[str]) -> List[Dict]:
    """Fallback plain-text log parsing."""
    steps = []
    for line in lines:
        tool_m = _TOOL_CALL_RE.search(line)
        if not tool_m:
            continue
        tool = tool_m.group(1)
        status_m = _STATUS_RE.search(line)
        outcome = status_m.group(1).lower() if status_m else "unknown"
        steps.append({
            "tool": tool,
            "args": [],
            "outcome": outcome,
            "used_aish_auto": bool(_AISH_RE.search(line)),
            "duration_ms": None,
        })
    return steps


def run_task_trace(repo_path: str, log_path: Optional[str] = None) -> Tuple[int, Dict]:
    resolved = log_path
    if not resolved:
        resolved = _default_log_path(repo_path)
    if not resolved:
        return 0, {
            "success": True,
            "task_trace_mode": "no_log_found",
            "steps": [],
            "summary": "No agent log file found in agent_logs/.",
        }

    abs_path = resolved if os.path.isabs(resolved) else os.path.join(repo_path, resolved)
    if not os.path.isfile(abs_path):
        return 2, {"error": "file_not_found", "target": resolved}

    lines = _read_lines(abs_path)
    steps = _parse_jsonl_steps(lines) or _parse_plain_steps(lines)

    tool_counts: Dict[str, int] = {}
    fallback_count = 0
    aish_auto_count = 0
    for step in steps:
        tool = step["tool"]
        tool_counts[tool] = tool_counts.get(tool, 0) + 1
        if step.get("used_aish_auto"):
            aish_auto_count += 1

    for line in lines:
        if _FALLBACK_RE.search(line):
            fallback_count += 1

    top_tools = sorted(tool_counts.items(), key=lambda x: -x[1])

    payload = {
        "success": True,
        "task_trace_mode": "agent_log_parse",
        "log_path": resolved,
        "total_steps": len(steps),
        "steps": steps,
        "tool_usage": [{"tool": t, "count": c} for t, c in top_tools],
        "fallback_events": fallback_count,
        "aish_auto_steps": aish_auto_count,
        "summary": (
            f"Parsed {len(steps)} tool steps from {os.path.basename(resolved)}; "
            f"top tool: {top_tools[0][0] if top_tools else 'none'}; "
            f"{fallback_count} fallback event(s); "
            f"{aish_auto_count} AISH-auto step(s)."
        ),
    }
    return 0, payload


def cmd_task_trace(repo_path: str, log_path: Optional[str] = None):
    code, payload = run_task_trace(repo_path, log_path)
    print(json.dumps(payload))
    return code, payload
