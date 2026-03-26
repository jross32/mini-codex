"""
zoo_visitor_thirst_tick - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_visitor_thirst_tick(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_visitor_thirst_tick")
    weather = rng.choice(["sunny","cloudy","hot","mild"])
    base_rate = {"sunny": 12, "hot": 18, "cloudy": 7, "mild": 8}[weather]
    hours = round(rng.uniform(0.5, 3.0), 1)
    thirst_increase = round(hours * base_rate, 1)
    thirst = min(100.0, round(thirst_increase + rng.uniform(0, 30), 1))
    payload: Dict = {
        "success": True,
        "thirst_level": thirst,
        "weather": weather,
        "weather_modifier": base_rate,
        "hours_without_drink": hours,
        "summary": f"Thirst: {thirst:.1f}/100 (weather={weather}, rate={base_rate}/h).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_visitor_thirst_tick(repo_path: str):
    code, payload = run_zoo_visitor_thirst_tick(repo_path)
    print(json.dumps(payload))
    return code, payload
