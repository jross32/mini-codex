"""
zoo_visitor_happiness_base_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_visitor_happiness_base_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_visitor_happiness_base_calc")
    exhibits_visited = rng.randint(1, 8)
    hours_in_zoo = round(rng.uniform(1.5, 6.0), 1)
    base_score = min(100, exhibits_visited * 10 + hours_in_zoo * 5)
    weather_mod = rng.choice([-5, 0, 0, 5])
    happiness = max(0, min(100, round(base_score + weather_mod)))
    payload: Dict = {
        "success": True,
        "happiness": happiness,
        "base_score": base_score,
        "exhibits_visited": exhibits_visited,
        "hours_in_zoo": hours_in_zoo,
        "weather_modifier": weather_mod,
        "summary": f"Visitor happiness: {happiness}/100 ({exhibits_visited} exhibits, {hours_in_zoo}h).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_visitor_happiness_base_calc(repo_path: str):
    code, payload = run_zoo_visitor_happiness_base_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
