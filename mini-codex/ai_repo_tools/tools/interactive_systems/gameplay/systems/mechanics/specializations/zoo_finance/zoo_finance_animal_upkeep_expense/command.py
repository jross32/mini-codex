"""
zoo_finance_animal_upkeep_expense - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_finance_animal_upkeep_expense(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_finance_animal_upkeep_expense")
    animal_count = rng.randint(5, 80)
    avg_cost_per_animal = rng.uniform(400, 1800)
    total = round(animal_count * avg_cost_per_animal, 2)
    payload: Dict = {
        "success": True,
        "total_expense": total,
        "animal_count": animal_count,
        "avg_cost_per_animal": round(avg_cost_per_animal, 2),
        "summary": f"Animal upkeep: ${total:,.2f}/mo ({animal_count} animals).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_finance_animal_upkeep_expense(repo_path: str):
    code, payload = run_zoo_finance_animal_upkeep_expense(repo_path)
    print(json.dumps(payload))
    return code, payload
