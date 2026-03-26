import json
import os
from typing import Any, Dict


DEFAULT_AGENT_CORE_STATE: Dict[str, Any] = {
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


def _state_path(repo_path: str) -> str:
    return os.path.join(repo_path, "agent_logs", "agent_core_state.json")


def load_agent_core_state(repo_path: str) -> Dict[str, Any]:
    merged = dict(DEFAULT_AGENT_CORE_STATE)
    path = _state_path(repo_path)
    if not os.path.isfile(path):
        return merged

    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        if not isinstance(raw, dict):
            return merged
        for key, value in raw.items():
            if key in merged:
                merged[key] = value
    except Exception:
        return merged

    return merged


def save_agent_core_state(repo_path: str, state: Dict[str, Any]) -> bool:
    path = _state_path(repo_path)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
        return True
    except Exception:
        return False
