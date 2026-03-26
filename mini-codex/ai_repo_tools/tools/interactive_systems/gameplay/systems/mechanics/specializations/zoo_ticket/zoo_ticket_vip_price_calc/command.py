"""
zoo_ticket_vip_price_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_ticket_vip_price_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_ticket_vip_price_calc")
    base_price = round(rng.uniform(10.0, 22.0), 2)
    premium_delta = round(rng.uniform(15.0, 45.0), 2)
    vip_price = round(base_price + premium_delta, 2)
    perks = rng.sample(["priority_entry","guided_tour","vip_lounge","animal_encounter","exclusive_feed_show"], k=3)
    payload: Dict = {
        "success": True,
        "base_price": base_price,
        "premium_delta": premium_delta,
        "vip_price": vip_price,
        "perks_included": perks,
        "summary": f"VIP ticket: ${vip_price:.2f} (base ${base_price:.2f} + ${premium_delta:.2f} premium).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_ticket_vip_price_calc(repo_path: str):
    code, payload = run_zoo_ticket_vip_price_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
