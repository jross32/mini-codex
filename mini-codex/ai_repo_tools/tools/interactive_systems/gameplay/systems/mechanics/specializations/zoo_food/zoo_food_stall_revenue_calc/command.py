"""
zoo_food_stall_revenue_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_food_stall_revenue_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_food_stall_revenue_calc")
    stall_type = rng.choice(["hotdog","icecream","burger_bar","restaurant","vending"])
    visitor_count = rng.randint(50, 500)
    conversion = rng.uniform(0.3, 0.8)
    avg_spend = {"hotdog":3.5,"icecream":2.5,"burger_bar":5.5,"restaurant":12.0,"vending":1.8}[stall_type]
    sales_count = round(visitor_count * conversion)
    daily_revenue = round(sales_count * avg_spend, 2)
    payload: Dict = {
        "success": True,
        "daily_revenue": daily_revenue,
        "stall_type": stall_type,
        "sales_count": sales_count,
        "avg_spend": avg_spend,
        "visitor_to_stall": visitor_count,
        "conversion_rate": round(conversion, 2),
        "summary": f"{stall_type} revenue: ${daily_revenue:.2f} ({sales_count} sales).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_food_stall_revenue_calc(repo_path: str):
    code, payload = run_zoo_food_stall_revenue_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
