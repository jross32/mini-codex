"""
zoo_staff_morale_tick - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_staff_morale_tick(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_staff_morale_tick")
    workload = rng.choice(["light","normal","heavy","extreme"])
    base_morale = rng.randint(40, 100)
    decay_rate = {"light": 1, "normal": 2, "heavy": 5, "extreme": 10}[workload]
    new_morale = max(0, base_morale - decay_rate)
    low_morale_flag = new_morale < 30
    payload: Dict = {
        "success": True,
        "morale": new_morale,
        "prev_morale": base_morale,
        "decay": decay_rate,
        "workload": workload,
        "low_morale_flag": low_morale_flag,
        "summary": f"Morale: {base_morale} → {new_morale} (workload={workload}).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_staff_morale_tick(repo_path: str):
    code, payload = run_zoo_staff_morale_tick(repo_path)
    print(json.dumps(payload))
    return code, payload
