"""
zoo_food_stall_queue_len_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_food_stall_queue_len_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_food_stall_queue_len_calc")
    visitor_density = rng.randint(10, 200)
    service_rate = rng.randint(15, 60)
    queue_length = max(0, round(visitor_density * 0.3 - service_rate * 0.4))
    wait_time = round(queue_length / max(service_rate, 1) * 60, 1)
    overflow_flag = queue_length > 30
    payload: Dict = {
        "success": True,
        "queue_length": queue_length,
        "wait_time_min": wait_time,
        "visitor_density": visitor_density,
        "service_rate_per_hour": service_rate,
        "overflow_flag": overflow_flag,
        "summary": f"Queue: {queue_length} people ({wait_time}min wait), overflow={overflow_flag}.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_food_stall_queue_len_calc(repo_path: str):
    code, payload = run_zoo_food_stall_queue_len_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
