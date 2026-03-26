"""
zoo_staff_skill_upgrade_cost_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_staff_skill_upgrade_cost_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_staff_skill_upgrade_cost_calc")
    from_level = rng.randint(1, 4)
    to_level = from_level + 1
    base_cost = 500
    upgrade_cost = round(base_cost * (from_level ** 1.5), 2)
    payload: Dict = {
        "success": True,
        "upgrade_cost": upgrade_cost,
        "from_level": from_level,
        "to_level": to_level,
        "training_days": from_level * 3,
        "summary": f"Skill upgrade {from_level}→{to_level}: ${upgrade_cost:.2f} ({from_level*3}d training).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_staff_skill_upgrade_cost_calc(repo_path: str):
    code, payload = run_zoo_staff_skill_upgrade_cost_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
