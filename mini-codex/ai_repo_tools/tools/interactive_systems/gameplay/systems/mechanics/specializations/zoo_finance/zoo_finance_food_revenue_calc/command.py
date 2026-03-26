"""
zoo_finance_food_revenue_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_finance_food_revenue_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_finance_food_revenue_calc")
    stall_count = rng.randint(3, 15)
    visitor_count = rng.randint(100, 2000)
    conversion = rng.uniform(0.4, 0.75)
    avg_spend = rng.uniform(2.5, 8.0)
    buyers = round(visitor_count * conversion)
    revenue = round(buyers * avg_spend, 2)
    payload: Dict = {
        "success": True,
        "revenue": revenue,
        "stall_count": stall_count,
        "visitor_count": visitor_count,
        "buyers": buyers,
        "avg_spend": round(avg_spend, 2),
        "conversion_rate": round(conversion, 2),
        "summary": f"Food revenue: ${revenue:,.2f} ({stall_count} stalls, {buyers} buyers).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_finance_food_revenue_calc(repo_path: str):
    code, payload = run_zoo_finance_food_revenue_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
