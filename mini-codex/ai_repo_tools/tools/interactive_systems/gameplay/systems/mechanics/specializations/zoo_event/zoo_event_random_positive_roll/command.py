"""
zoo_event_random_positive_roll - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_event_random_positive_roll(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_event_random_positive_roll")
    events = [
        ("viral_social_post",    1.3, 1.2, 3),
        ("celebrity_visit",      1.5, 1.4, 1),
        ("wildlife_doc_filming", 1.2, 1.1, 7),
        ("baby_animal_birth",    1.6, 1.0, 14),
        ("school_partnership",   1.1, 1.05, 30),
        ("rare_species_arrival", 1.4, 1.0, 60),
    ]
    event_name, v_boost, r_boost, dur = rng.choice(events)
    payload: Dict = {
        "success": True,
        "event_name": event_name,
        "visitor_boost": v_boost,
        "revenue_boost": r_boost,
        "duration_days": dur,
        "summary": f"POSITIVE EVENT: [{event_name}] v×{v_boost} r×{r_boost} for {dur}d.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_event_random_positive_roll(repo_path: str):
    code, payload = run_zoo_event_random_positive_roll(repo_path)
    print(json.dumps(payload))
    return code, payload
