"""
zoo_event_random_negative_roll - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_event_random_negative_roll(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_event_random_negative_roll")
    events = [
        ("animal_escape",   8000, 0.6, "critical"),
        ("storm_damage",    5000, 0.8, "high"),
        ("staff_strike",    2000, 0.7, "high"),
        ("disease_scare",   3000, 0.5, "critical"),
        ("vandalism",       1200, 0.9, "medium"),
        ("water_outage",     800, 0.85, "medium"),
    ]
    event_name, cost, v_penalty, severity = rng.choice(events)
    payload: Dict = {
        "success": True,
        "event_name": event_name,
        "repair_cost": cost,
        "visitor_penalty": v_penalty,
        "severity": severity,
        "summary": f"NEGATIVE EVENT: [{event_name}] cost=${cost:,}, visitors×{v_penalty} [{severity}].",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_event_random_negative_roll(repo_path: str):
    code, payload = run_zoo_event_random_negative_roll(repo_path)
    print(json.dumps(payload))
    return code, payload
