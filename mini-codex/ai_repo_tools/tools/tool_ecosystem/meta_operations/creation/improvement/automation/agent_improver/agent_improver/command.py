import json
import os
import time
from typing import Dict, List, Optional, Tuple


_DEFAULT_CORE_STATE = {
    "version": 1,
    "success_usefulness": 4,
    "failure_usefulness": 1,
    "success_uncertainty_reduction": 3,
    "failure_uncertainty_reduction": 1,
    "success_next_step_quality": 3,
    "failure_next_step_quality": 1,
    "warning_penalty": 1,
    "failure_penalty": 1,
    "toolmaker_max_failures_per_candidate": 1,
}


_BOUNDS = {
    "success_usefulness": (2, 6),
    "failure_usefulness": (1, 4),
    "success_uncertainty_reduction": (2, 6),
    "failure_uncertainty_reduction": (1, 4),
    "success_next_step_quality": (2, 6),
    "failure_next_step_quality": (1, 4),
    "warning_penalty": (0, 3),
    "failure_penalty": (0, 4),
    "toolmaker_max_failures_per_candidate": (1, 3),
}


def _safe_load_json(path: str, default):
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as fh:
            parsed = json.load(fh)
        return parsed
    except Exception:
        return default


def _safe_write_json(path: str, payload: Dict) -> bool:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        return True
    except Exception:
        return False


def _merge_state(raw: Dict) -> Dict:
    merged = dict(_DEFAULT_CORE_STATE)
    if isinstance(raw, dict):
        for key, value in raw.items():
            if key in merged:
                merged[key] = value
    return merged


def _clamp_value(key: str, value: int) -> int:
    lo, hi = _BOUNDS.get(key, (value, value))
    return max(lo, min(hi, int(value)))


def _load_recommendations(repo_path: str, recommendations_json: Optional[str]) -> List[Dict]:
    if recommendations_json:
        try:
            parsed = json.loads(recommendations_json)
            if isinstance(parsed, list):
                return [x for x in parsed if isinstance(x, dict)]
        except Exception:
            return []

    audit_path = os.path.join(repo_path, "agent_logs", "agent_core_last_audit.json")
    audit = _safe_load_json(audit_path, {})
    recs = audit.get("recommendations", []) if isinstance(audit, dict) else []
    return [x for x in recs if isinstance(x, dict)]


def run_agent_improver(repo_path: str, recommendations_json: Optional[str] = None) -> Tuple[int, Dict]:
    t0 = time.monotonic()

    state_path = os.path.join(repo_path, "agent_logs", "agent_core_state.json")
    history_path = os.path.join(repo_path, "agent_logs", "agent_core_history.json")

    before = _merge_state(_safe_load_json(state_path, {}))
    after = dict(before)

    recommendations = _load_recommendations(repo_path, recommendations_json)
    applied: List[Dict] = []

    for rec in recommendations:
        key = rec.get("key")
        value = rec.get("value")
        if key not in _BOUNDS or value is None:
            continue
        old_val = int(after.get(key, before.get(key, 0)) or 0)
        new_val = _clamp_value(key, int(value))
        if new_val != old_val:
            after[key] = new_val
            applied.append(
                {
                    "key": key,
                    "before": old_val,
                    "after": new_val,
                    "reason": rec.get("reason", ""),
                }
            )

    saved = _safe_write_json(state_path, after)

    history = _safe_load_json(history_path, [])
    if not isinstance(history, list):
        history = []
    history.append(
        {
            "timestamp_epoch": int(time.time()),
            "applied": applied,
            "before": before,
            "after": after,
        }
    )
    if len(history) > 200:
        history = history[-200:]
    history_saved = _safe_write_json(history_path, {"events": history})

    elapsed_ms = round((time.monotonic() - t0) * 1000)
    payload = {
        "success": bool(saved),
        "tool": "agent_improver",
        "applied": applied,
        "applied_count": len(applied),
        "state_saved": saved,
        "history_saved": history_saved,
        "agent_core_before": before,
        "agent_core_after": after,
        "elapsed_ms": elapsed_ms,
        "summary": (
            f"Agent core improver applied {len(applied)} tuning change(s)."
            if saved
            else "Agent core improver failed to save state."
        ),
    }
    return (0 if saved else 2), payload


def cmd_agent_improver(repo_path: str, recommendations_json: Optional[str] = None):
    code, payload = run_agent_improver(repo_path, recommendations_json)
    print(json.dumps(payload))
    return code, payload
