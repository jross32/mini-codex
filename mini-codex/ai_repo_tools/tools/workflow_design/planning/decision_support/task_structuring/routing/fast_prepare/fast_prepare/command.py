import json
from typing import Dict, List, Optional, Tuple

from tools.planning.fast_process.command import run_fast_process


def _build_prep_steps(primary_doc: Optional[str], followups: List[str], next_actions: List[str]) -> List[str]:
    steps: List[str] = []

    if primary_doc:
        steps.append(f"read:{primary_doc}")

    for f in followups[:3]:
        steps.append(f"read:{f}")

    for action in next_actions:
        if action not in steps:
            steps.append(action)

    if "run:env_check" not in steps:
        steps.append("run:env_check")

    return steps[:8]


def _confirmed_checks(payload: Dict) -> Dict:
    checks = {
        "has_primary_or_fallback": bool(payload.get("primary_orientation_doc") or payload.get("next_actions")),
        "has_prep_steps": bool(payload.get("preparation_steps")),
        "step_count_in_bounds": 1 <= len(payload.get("preparation_steps", [])) <= 8,
    }
    checks["all_passed"] = all(checks.values())
    return checks


def run_fast_prepare(repo_path: str, max_files: Optional[int] = None) -> Tuple[int, Dict]:
    code, process = run_fast_process(repo_path, max_files=max_files)
    if code != 0:
        payload = {
            "success": False,
            "error": "upstream_fast_process_failed",
            "process": process,
        }
        return code, payload

    primary_doc = process.get("primary_orientation_doc")
    followups = process.get("recommended_followups", [])
    next_actions = process.get("next_actions", [])

    prep_steps = _build_prep_steps(primary_doc, followups, next_actions)

    payload = {
        "success": True,
        "repo_path": repo_path,
        "prepare_mode": "deterministic_preflight_plan",
        "primary_orientation_doc": primary_doc,
        "recommended_followups": followups,
        "preparation_steps": prep_steps,
        "estimated_read_steps": len([s for s in prep_steps if s.startswith("read:")]),
        "estimated_run_steps": len([s for s in prep_steps if s.startswith("run:")]),
        "summary": (
            f"Prepared {len(prep_steps)} deterministic preflight steps; "
            f"primary doc: {primary_doc or 'none'}."
        ),
    }
    payload["confirmed_checks"] = _confirmed_checks(payload)
    return 0, payload


def cmd_fast_prepare(repo_path: str, max_files: Optional[int] = None):
    code, payload = run_fast_prepare(repo_path, max_files=max_files)
    print(json.dumps(payload))
    return code, payload
