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


def _safe_load_json(path: str, default):
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as fh:
            parsed = json.load(fh)
        return parsed
    except Exception:
        return default


def _merge_core_state(raw: Dict) -> Dict:
    merged = dict(_DEFAULT_CORE_STATE)
    if isinstance(raw, dict):
        for key, value in raw.items():
            if key in merged:
                merged[key] = value
    return merged


def _build_recommendations(summary: Dict, core_state: Dict) -> List[Dict]:
    failure_counts = summary.get("failure_counts", {}) if isinstance(summary, dict) else {}
    weak_counts = summary.get("weak_result_counts", {}) if isinstance(summary, dict) else {}
    gap_counts = summary.get("gap_signal_counts", {}) if isinstance(summary, dict) else {}

    failures = sum(int(v or 0) for v in failure_counts.values())
    weak = sum(int(v or 0) for v in weak_counts.values())
    gaps = sum(int(v or 0) for v in gap_counts.values())

    recommendations: List[Dict] = []

    if failures > 0:
        recommendations.append(
            {
                "key": "failure_penalty",
                "value": min(4, int(core_state.get("failure_penalty", 1) or 1) + 1),
                "reason": f"Observed {failures} failed tool runs in observation summary.",
            }
        )

    if weak >= 8:
        recommendations.append(
            {
                "key": "warning_penalty",
                "value": min(3, int(core_state.get("warning_penalty", 1) or 1) + 1),
                "reason": f"Observed {weak} weak-result signals; increase caution penalty.",
            }
        )

    if gaps >= 10:
        recommendations.append(
            {
                "key": "toolmaker_max_failures_per_candidate",
                "value": min(3, int(core_state.get("toolmaker_max_failures_per_candidate", 1) or 1) + 1),
                "reason": f"Observed {gaps} gap signals; allow one extra candidate retry before skipping.",
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "key": "no_change",
                "value": None,
                "reason": "No tuning needed from current observation signal levels.",
            }
        )

    return recommendations


def run_agent_audit(repo_path: str, mode: Optional[str] = None) -> Tuple[int, Dict]:
    t0 = time.monotonic()

    summary_path = os.path.join(repo_path, "agent_logs", "tool_observations_summary.json")
    core_state_path = os.path.join(repo_path, "agent_logs", "agent_core_state.json")

    summary = _safe_load_json(summary_path, {})
    core_state = _merge_core_state(_safe_load_json(core_state_path, {}))
    recommendations = _build_recommendations(summary, core_state)

    failure_counts = summary.get("failure_counts", {}) if isinstance(summary, dict) else {}
    weak_counts = summary.get("weak_result_counts", {}) if isinstance(summary, dict) else {}
    gap_counts = summary.get("gap_signal_counts", {}) if isinstance(summary, dict) else {}

    failures = sum(int(v or 0) for v in failure_counts.values())
    weak = sum(int(v or 0) for v in weak_counts.values())
    gaps = sum(int(v or 0) for v in gap_counts.values())
    health_score = max(0, 100 - (failures * 3) - weak - (gaps // 2))

    # Save latest recommendations for the improver to consume deterministically.
    audit_dump = {
        "recommendations": recommendations,
        "health_score": health_score,
        "timestamp_epoch": int(time.time()),
    }
    try:
        os.makedirs(os.path.join(repo_path, "agent_logs"), exist_ok=True)
        with open(os.path.join(repo_path, "agent_logs", "agent_core_last_audit.json"), "w", encoding="utf-8") as fh:
            json.dump(audit_dump, fh, indent=2)
    except Exception:
        pass

    elapsed_ms = round((time.monotonic() - t0) * 1000)
    payload = {
        "success": True,
        "tool": "agent_audit",
        "mode": mode or "scan",
        "health_score": health_score,
        "recommendations": recommendations,
        "observed_failures": failures,
        "observed_weak_results": weak,
        "observed_gap_signals": gaps,
        "elapsed_ms": elapsed_ms,
        "summary": (
            f"Agent core audit score {health_score}/100 with {len(recommendations)} recommendation(s)."
        ),
    }
    return 0, payload


def cmd_agent_audit(repo_path: str, mode: Optional[str] = None):
    code, payload = run_agent_audit(repo_path, mode)
    print(json.dumps(payload))
    return code, payload
