"""
zoo_ticket_child_price_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_ticket_child_price_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_ticket_child_price_calc")
    adult_price = round(rng.uniform(10.0, 22.0), 2)
    discount_pct = rng.choice([40, 45, 50])
    child_price = round(adult_price * (1 - discount_pct / 100), 2)
    payload: Dict = {
        "success": True,
        "adult_price": adult_price,
        "child_price": child_price,
        "discount_pct": discount_pct,
        "summary": f"Child ticket: ${child_price:.2f} ({discount_pct}% off adult ${adult_price:.2f}).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_ticket_child_price_calc(repo_path: str):
    code, payload = run_zoo_ticket_child_price_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
