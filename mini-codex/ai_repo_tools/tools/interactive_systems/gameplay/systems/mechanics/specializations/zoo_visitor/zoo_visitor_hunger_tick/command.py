"""
zoo_visitor_hunger_tick - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_visitor_hunger_tick(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_visitor_hunger_tick")
    hours_since_meal = round(rng.uniform(0.5, 4.0), 1)
    base_rate = 8
    hunger_increase = round(hours_since_meal * base_rate, 1)
    current_hunger = round(rng.uniform(0, 60) + hunger_increase, 1)
    current_hunger = min(100.0, current_hunger)
    fed_flag = current_hunger >= 70
    payload: Dict = {
        "success": True,
        "hunger_level": current_hunger,
        "decay_per_hour": base_rate,
        "hours_since_meal": hours_since_meal,
        "fed_flag": fed_flag,
        "summary": f"Hunger: {current_hunger:.1f}/100 (fed_flag={fed_flag}).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_visitor_hunger_tick(repo_path: str):
    code, payload = run_zoo_visitor_hunger_tick(repo_path)
    print(json.dumps(payload))
    return code, payload
