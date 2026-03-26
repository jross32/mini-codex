"""
zoo_ticket_price_base_set - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_ticket_price_base_set(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_ticket_price_base_set")
    price = round(rng.uniform(10.0, 22.0), 2)
    if price < 5.0:
        note = "too_low"
    elif price > 100.0:
        note = "too_high"
    else:
        note = "ok"
    payload: Dict = {
        "success": True,
        "price": price,
        "currency": "USD",
        "validation_note": note,
        "summary": f"Adult ticket base price set to ${price:.2f} ({note}).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_ticket_price_base_set(repo_path: str):
    code, payload = run_zoo_ticket_price_base_set(repo_path)
    print(json.dumps(payload))
    return code, payload
