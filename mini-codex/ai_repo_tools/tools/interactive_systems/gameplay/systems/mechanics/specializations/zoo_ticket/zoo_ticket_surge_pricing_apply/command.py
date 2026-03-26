"""
zoo_ticket_surge_pricing_apply - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_ticket_surge_pricing_apply(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_ticket_surge_pricing_apply")
    base_price = round(rng.uniform(10.0, 22.0), 2)
    occupancy_pct = rng.randint(50, 110)
    if occupancy_pct >= 100:
        tier = "maxed"
        multiplier = 1.5
    elif occupancy_pct >= 85:
        tier = "high"
        multiplier = 1.25
    elif occupancy_pct >= 70:
        tier = "medium"
        multiplier = 1.1
    else:
        tier = "normal"
        multiplier = 1.0
    final_price = round(base_price * multiplier, 2)
    payload: Dict = {
        "success": True,
        "base_price": base_price,
        "occupancy_pct": min(occupancy_pct, 100),
        "surge_multiplier": multiplier,
        "tier": tier,
        "final_price": final_price,
        "summary": f"Surge [{tier}] x{multiplier}: ${base_price:.2f} → ${final_price:.2f}.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_ticket_surge_pricing_apply(repo_path: str):
    code, payload = run_zoo_ticket_surge_pricing_apply(repo_path)
    print(json.dumps(payload))
    return code, payload
