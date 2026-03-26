"""
zoo_animal_health_tick - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_animal_health_tick(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_animal_health_tick")
    current_health = round(rng.uniform(50, 100), 1)
    keeper_skill = rng.choice(["novice","trained","expert"])
    decay = {"novice": 3.5, "trained": 1.5, "expert": 0.5}[keeper_skill]
    new_health = round(max(0, current_health - decay), 1)
    if new_health < 30:
        status = "critical"
    elif new_health < 60:
        status = "poor"
    else:
        status = "healthy"
    payload: Dict = {
        "success": True,
        "health": new_health,
        "prev_health": current_health,
        "decay_amount": decay,
        "keeper_skill": keeper_skill,
        "status": status,
        "summary": f"Health tick: {current_health:.1f} → {new_health:.1f} ({status}).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_animal_health_tick(repo_path: str):
    code, payload = run_zoo_animal_health_tick(repo_path)
    print(json.dumps(payload))
    return code, payload
