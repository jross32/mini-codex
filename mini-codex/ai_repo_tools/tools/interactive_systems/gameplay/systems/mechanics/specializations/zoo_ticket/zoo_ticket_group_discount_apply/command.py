"""
zoo_ticket_group_discount_apply - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_ticket_group_discount_apply(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_ticket_group_discount_apply")
    group_size = rng.randint(8, 40)
    subtotal = round(rng.uniform(120, 600), 2)
    if group_size >= 30:
        tier = "large"
        pct = 25
    elif group_size >= 15:
        tier = "medium"
        pct = 15
    else:
        tier = "small"
        pct = 10
    savings = round(subtotal * pct / 100, 2)
    discounted = round(subtotal - savings, 2)
    payload: Dict = {
        "success": True,
        "group_size": group_size,
        "original_subtotal": subtotal,
        "discounted_total": discounted,
        "savings": savings,
        "discount_pct": pct,
        "discount_tier": tier,
        "summary": f"Group of {group_size} ({tier}): saved ${savings:.2f} → total ${discounted:.2f}.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_ticket_group_discount_apply(repo_path: str):
    code, payload = run_zoo_ticket_group_discount_apply(repo_path)
    print(json.dumps(payload))
    return code, payload
