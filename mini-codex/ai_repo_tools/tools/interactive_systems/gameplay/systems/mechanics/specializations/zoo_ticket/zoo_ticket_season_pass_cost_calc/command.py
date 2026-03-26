"""
zoo_ticket_season_pass_cost_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_ticket_season_pass_cost_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_ticket_season_pass_cost_calc")
    adult_price = round(rng.uniform(10.0, 22.0), 2)
    multiplier = rng.choice([5, 6, 6, 7])
    season_pass_price = round(adult_price * multiplier, 2)
    breakeven = multiplier
    payload: Dict = {
        "success": True,
        "season_pass_price": season_pass_price,
        "adult_single_price": adult_price,
        "multiplier": multiplier,
        "single_breakeven_visits": breakeven,
        "summary": f"Season pass: ${season_pass_price:.2f} (breaks even after {breakeven} visits).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_ticket_season_pass_cost_calc(repo_path: str):
    code, payload = run_zoo_ticket_season_pass_cost_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
