"""
zoo_food_stock_depletion_check - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_food_stock_depletion_check(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_food_stock_depletion_check")
    stall_type = rng.choice(["hotdog","icecream","burger_bar","vending"])
    stock_start = rng.randint(50, 300)
    sold = rng.randint(0, stock_start + 50)
    stock_remaining = max(0, stock_start - sold)
    depleted = stock_remaining == 0
    restock_cost = round((stock_start * 0.6) * rng.uniform(0.9, 1.1), 2)
    payload: Dict = {
        "success": True,
        "depleted": depleted,
        "stall_type": stall_type,
        "stock_start": stock_start,
        "units_sold": min(sold, stock_start),
        "stock_remaining": stock_remaining,
        "restock_cost": restock_cost,
        "summary": f"Stock [{stall_type}]: {stock_remaining} remaining {'(DEPLETED)' if depleted else ''}, restock=${restock_cost:.2f}.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_food_stock_depletion_check(repo_path: str):
    code, payload = run_zoo_food_stock_depletion_check(repo_path)
    print(json.dumps(payload))
    return code, payload
