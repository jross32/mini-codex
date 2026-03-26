import json
import os
from datetime import datetime, timezone


OBSERVATION_LOG_REL = "agent_logs/tool_observations.jsonl"
OBSERVATION_SUMMARY_REL = "agent_logs/tool_observations_summary.json"


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _classify_failure(stderr_text):
    text = (stderr_text or "").lower()
    if "file not found" in text or "no such file" in text:
        return "missing_path"
    if "missing argument" in text or "requires file argument" in text:
        return "missing_argument"
    if "jsondecodeerror" in text or "could not be parsed" in text:
        return "parse_error"
    if "timeout" in text:
        return "timeout"
    if "permission denied" in text or "access is denied" in text:
        return "permission"
    if "module not found" in text or "no module named" in text:
        return "missing_dependency"
    if "failed" in text or "error" in text or "assertionerror" in text:
        return "test_failure"
    if text:
        return "runtime_error"
    return "unknown"


def _weak_and_gaps(tool_name, payload):
    weak = False
    gaps = []
    if not isinstance(payload, dict):
        return weak, gaps

    if tool_name == "repo_map" and payload.get("file_count", 0) == 0:
        weak = True
        gaps.append("no_files_listed")

    if tool_name == "test_select" and not payload.get("recommended_files"):
        weak = True
        gaps.append("no_recommendations")

    if tool_name in {"ai_read", "artifact_read"} and payload.get("parse_status") == "fallback":
        weak = True
        gaps.append("parse_fallback")

    if payload.get("line_count") == 0:
        weak = True
        gaps.append("empty_content")

    if tool_name == "cmd_run":
        if payload.get("failed_count") and payload["failed_count"] > 0:
            weak = True
            gaps.append("test_failures")
        if payload.get("error") == "timeout":
            gaps.append("execution_timeout")

    return weak, sorted(set(gaps))


def _load_summary(path):
    if not os.path.exists(path):
        return {
            "tool_counts": {},
            "failure_counts": {},
            "weak_result_counts": {},
            "gap_signal_counts": {},
            "last_updated": None,
        }

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass

    return {
        "tool_counts": {},
        "failure_counts": {},
        "weak_result_counts": {},
        "gap_signal_counts": {},
        "last_updated": None,
    }


def _bump(counter, key):
    counter[key] = counter.get(key, 0) + 1


def observe_tool_run(repo_path, tool_name, tool_args, exit_code, payload=None, stderr_text=""):
    if not repo_path:
        return

    weak_result, gap_signals = _weak_and_gaps(tool_name, payload)
    success = exit_code == 0

    event = {
        "timestamp": _now_iso(),
        "tool": tool_name,
        "args_count": len(tool_args or []),
        "success": success,
        "exit_code": exit_code,
        "failure_category": None if success else _classify_failure(stderr_text),
        "weak_result": weak_result,
        "gap_signals": gap_signals,
    }

    log_path = os.path.join(repo_path, OBSERVATION_LOG_REL)
    summary_path = os.path.join(repo_path, OBSERVATION_SUMMARY_REL)

    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    summary = _load_summary(summary_path)
    _bump(summary.setdefault("tool_counts", {}), tool_name)

    if not success:
        _bump(summary.setdefault("failure_counts", {}), event["failure_category"] or "unknown")

    if weak_result:
        _bump(summary.setdefault("weak_result_counts", {}), tool_name)

    for signal in gap_signals:
        _bump(summary.setdefault("gap_signal_counts", {}), signal)

    summary["last_updated"] = event["timestamp"]

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
