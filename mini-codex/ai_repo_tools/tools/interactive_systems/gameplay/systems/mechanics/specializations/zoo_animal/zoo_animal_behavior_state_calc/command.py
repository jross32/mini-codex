"""
zoo_animal_behavior_state_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_animal_behavior_state_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_animal_behavior_state_calc")
    health = rng.randint(30, 100)
    enrichment = rng.randint(0, 100)
    score = health * 0.6 + enrichment * 0.4
    if score >= 80:
        state = "playing"
        visitor_bonus = 15
    elif score >= 65:
        state = "active"
        visitor_bonus = 10
    elif score >= 45:
        state = "resting"
        visitor_bonus = 3
    else:
        state = "lethargic"
        visitor_bonus = -5
    payload: Dict = {
        "success": True,
        "behavior_state": state,
        "enrichment_score": enrichment,
        "health_score": health,
        "composite_score": round(score, 1),
        "visitor_bonus": visitor_bonus,
        "summary": f"Behavior: {state} (+{visitor_bonus} visitor bonus).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_animal_behavior_state_calc(repo_path: str):
    code, payload = run_zoo_animal_behavior_state_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
