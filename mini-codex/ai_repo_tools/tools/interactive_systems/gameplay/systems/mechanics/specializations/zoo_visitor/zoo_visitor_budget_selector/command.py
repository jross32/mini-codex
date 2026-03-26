"""
zoo_visitor_budget_selector - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_visitor_budget_selector(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_visitor_budget_selector")
    tiers = [("low",15,25),("mid",30,55),("high",60,100),("whale",120,250)]
    weights = [30, 45, 20, 5]
    tier, low, high = rng.choices(tiers, weights=weights, k=1)[0]
    cap = round(rng.uniform(low, high), 2)
    payload: Dict = {
        "success": True,
        "budget_tier": tier,
        "daily_spend_cap": cap,
        "food_share": round(cap * 0.4, 2),
        "merch_share": round(cap * 0.2, 2),
        "summary": f"Budget tier: {tier} (cap ${cap:.2f}/day).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_visitor_budget_selector(repo_path: str):
    code, payload = run_zoo_visitor_budget_selector(repo_path)
    print(json.dumps(payload))
    return code, payload
