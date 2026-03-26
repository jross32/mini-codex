"""
zoo_staff_type_selector - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_staff_type_selector(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_staff_type_selector")
    staff_types = [
        ("zookeeper",  2400, 2),
        ("vet",        4200, 3),
        ("janitor",    1800, 1),
        ("guide",      2200, 2),
        ("security",   2100, 2),
        ("cashier",    1900, 1),
    ]
    weights = [30, 15, 20, 15, 10, 10]
    staff_type, base_salary, skill_level = rng.choices(staff_types, weights=weights, k=1)[0]
    payload: Dict = {
        "success": True,
        "staff_type": staff_type,
        "base_salary": base_salary,
        "skill_level": skill_level,
        "max_skill_level": 5,
        "summary": f"Staff: {staff_type} (skill {skill_level}/5, salary ${base_salary}/mo).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_staff_type_selector(repo_path: str):
    code, payload = run_zoo_staff_type_selector(repo_path)
    print(json.dumps(payload))
    return code, payload
