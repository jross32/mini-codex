"""
zoo_animal_upkeep_cost_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_animal_upkeep_cost_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_animal_upkeep_cost_calc")
    species_costs = {
        "feed_per_day": round(rng.uniform(8, 40), 2),
        "vet_per_month": round(rng.uniform(200, 800), 2),
        "enrichment_per_month": round(rng.uniform(50, 200), 2),
    }
    daily_total = species_costs["feed_per_day"] + species_costs["vet_per_month"] / 30 + species_costs["enrichment_per_month"] / 30
    monthly = round(daily_total * 30, 2)
    payload: Dict = {
        "success": True,
        "monthly_upkeep": monthly,
        "feed_cost_daily": species_costs["feed_per_day"],
        "vet_cost_monthly": species_costs["vet_per_month"],
        "enrichment_monthly": species_costs["enrichment_per_month"],
        "summary": f"Monthly upkeep: ${monthly:,.2f}.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_animal_upkeep_cost_calc(repo_path: str):
    code, payload = run_zoo_animal_upkeep_cost_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
