"""
zoo_staff_fatigue_tick - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_staff_fatigue_tick(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_staff_fatigue_tick")
    shift_hours = rng.choice([6, 8, 10, 12])
    tasks_done = rng.randint(5, 30)
    base_fatigue = shift_hours * 5
    task_fatigue = tasks_done * 1.5
    total_fatigue = round(base_fatigue + task_fatigue, 1)
    fatigue_pct = min(100, total_fatigue)
    exhausted_flag = fatigue_pct >= 90
    payload: Dict = {
        "success": True,
        "fatigue": fatigue_pct,
        "increment": total_fatigue,
        "shift_hours": shift_hours,
        "tasks_done": tasks_done,
        "exhausted_flag": exhausted_flag,
        "summary": f"Fatigue: {fatigue_pct:.1f}% after {shift_hours}h shift ({tasks_done} tasks).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_staff_fatigue_tick(repo_path: str):
    code, payload = run_zoo_staff_fatigue_tick(repo_path)
    print(json.dumps(payload))
    return code, payload
