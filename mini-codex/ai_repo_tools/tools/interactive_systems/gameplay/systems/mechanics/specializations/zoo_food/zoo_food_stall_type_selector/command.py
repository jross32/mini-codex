"""
zoo_food_stall_type_selector - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_food_stall_type_selector(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_food_stall_type_selector")
    stalls = [
        ("hotdog",       800,  150, 3.5),
        ("icecream",     600,  100, 2.5),
        ("burger_bar",  3500,  250, 5.5),
        ("restaurant",  8000,   80, 12.0),
        ("vending",      300,  200, 1.8),
    ]
    weights = [30, 25, 20, 10, 15]
    stall_type, setup_cost, daily_capacity, avg_spend = rng.choices(stalls, weights=weights, k=1)[0]
    payload: Dict = {
        "success": True,
        "stall_type": stall_type,
        "setup_cost": setup_cost,
        "daily_capacity": daily_capacity,
        "avg_spend_per_visitor": avg_spend,
        "summary": f"Food stall: {stall_type} (cost ${setup_cost}, cap {daily_capacity}/day).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_food_stall_type_selector(repo_path: str):
    code, payload = run_zoo_food_stall_type_selector(repo_path)
    print(json.dumps(payload))
    return code, payload
