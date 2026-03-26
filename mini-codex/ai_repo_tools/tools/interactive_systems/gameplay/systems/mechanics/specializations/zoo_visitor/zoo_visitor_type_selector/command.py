"""
zoo_visitor_type_selector - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_visitor_type_selector(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_visitor_type_selector")
    types = [("family",4,50),("solo",1,30),("group",8,40),("school",25,25),("couple",2,45)]
    weights = [40, 15, 20, 15, 10]
    chosen = rng.choices(types, weights=weights, k=1)[0]
    visitor_type, group_size_base, budget_base = chosen
    group_size = group_size_base + rng.randint(-1, 1)
    budget_tier = "low" if budget_base < 35 else ("mid" if budget_base < 45 else "high")
    payload: Dict = {
        "success": True,
        "visitor_type": visitor_type,
        "group_size": max(1, group_size),
        "budget_tier": budget_tier,
        "daily_spend_estimate": round(budget_base * 1.0 + rng.uniform(-5, 10), 2),
        "summary": f"Visitor: {visitor_type} group of {max(1,group_size)} [{budget_tier} budget].",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_visitor_type_selector(repo_path: str):
    code, payload = run_zoo_visitor_type_selector(repo_path)
    print(json.dumps(payload))
    return code, payload
