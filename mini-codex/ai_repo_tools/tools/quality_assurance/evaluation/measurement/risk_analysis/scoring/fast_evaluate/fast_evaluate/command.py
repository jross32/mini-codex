import json
import time
from typing import Dict, Optional, Tuple

from tools.planning.fast_prepare.command import run_fast_prepare


def _score_payload(payload: Dict) -> Dict:
    prep_steps = payload.get("preparation_steps", [])
    has_primary = bool(payload.get("primary_orientation_doc"))
    has_followups = bool(payload.get("recommended_followups"))
    checks = payload.get("confirmed_checks", {})

    score = 0
    score += 40 if has_primary else 10
    score += 25 if has_followups else 5
    score += 25 if checks.get("all_passed") else 0
    score += 10 if len(prep_steps) >= 3 else 0

    score = max(0, min(100, score))

    if score >= 85:
        rating = "strong"
    elif score >= 65:
        rating = "good"
    elif score >= 45:
        rating = "fair"
    else:
        rating = "weak"

    return {
        "score": score,
        "rating": rating,
    }


def run_fast_evaluate(repo_path: str, max_files: Optional[int] = None, include_legacy_timing: bool = False) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    code, prep = run_fast_prepare(repo_path, max_files=max_files)
    if code != 0:
        payload = {
            "success": False,
            "error": "upstream_fast_prepare_failed",
            "prepare": prep,
        }
        return code, payload

    scoring = _score_payload(prep)
    duration = round(time.monotonic() - t0, 4)

    payload = {
        "success": True,
        "repo_path": repo_path,
        "evaluate_mode": "deterministic_preflight_evaluation",
        "score": scoring["score"],
        "rating": scoring["rating"],
        "duration_seconds": duration,
        "primary_orientation_doc": prep.get("primary_orientation_doc"),
        "recommended_followups": prep.get("recommended_followups", [])[:5],
        "preparation_steps": prep.get("preparation_steps", [])[:8],
        "confirmed_checks": prep.get("confirmed_checks", {}),
        "summary": (
            f"Evaluation score {scoring['score']}/100 ({scoring['rating']}); "
            f"steps={len(prep.get('preparation_steps', []))}."
        ),
    }

    if include_legacy_timing:
        # Bounded side-by-side timing snapshot versus deterministic baseline.
        payload["legacy_timing_note"] = "Legacy timing not executed here; use prior benchmark harness for full comparison."

    return 0, payload


def cmd_fast_evaluate(repo_path: str, max_files: Optional[int] = None):
    code, payload = run_fast_evaluate(repo_path, max_files=max_files)
    print(json.dumps(payload))
    return code, payload
