"""
zoo_visitor_happiness_crowding_penalty - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_visitor_happiness_crowding_penalty(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_visitor_happiness_crowding_penalty")
    capacity = rng.randint(40, 120)
    current = rng.randint(20, 150)
    ratio = current / max(capacity, 1)
    if ratio > 1.5:
        tier = "severe"
        penalty = -25
    elif ratio > 1.2:
        tier = "high"
        penalty = -15
    elif ratio > 1.0:
        tier = "moderate"
        penalty = -8
    else:
        tier = "ok"
        penalty = 0
    payload: Dict = {
        "success": True,
        "penalty": penalty,
        "crowding_ratio": round(ratio, 2),
        "current_visitors": current,
        "exhibit_capacity": capacity,
        "tier": tier,
        "summary": f"Crowding [{tier}]: {penalty} happiness penalty (ratio {ratio:.2f}).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_visitor_happiness_crowding_penalty(repo_path: str):
    code, payload = run_zoo_visitor_happiness_crowding_penalty(repo_path)
    print(json.dumps(payload))
    return code, payload
