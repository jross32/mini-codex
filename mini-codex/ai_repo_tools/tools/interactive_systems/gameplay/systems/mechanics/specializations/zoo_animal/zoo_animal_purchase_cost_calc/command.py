"""
zoo_animal_purchase_cost_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_animal_purchase_cost_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_animal_purchase_cost_calc")
    rarity_base = {"common": 2000, "uncommon": 6000, "rare": 18000}
    rarity = rng.choice(["common","uncommon","rare"])
    base = rarity_base[rarity]
    negotiated = round(base * rng.uniform(0.85, 1.15), 2)
    payload: Dict = {
        "success": True,
        "rarity": rarity,
        "base_cost": base,
        "purchase_cost": negotiated,
        "negotiation_factor": round(negotiated / base, 3),
        "summary": f"Purchase cost ({rarity}): ${negotiated:,.2f}.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_animal_purchase_cost_calc(repo_path: str):
    code, payload = run_zoo_animal_purchase_cost_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
