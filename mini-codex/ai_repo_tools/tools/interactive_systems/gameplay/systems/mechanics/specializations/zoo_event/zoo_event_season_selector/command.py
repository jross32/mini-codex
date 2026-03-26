"""
zoo_event_season_selector - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_event_season_selector(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_event_season_selector")
    seasons = [
        ("spring", 1.15, "cherry_blossom_festival"),
        ("summer", 1.35, "summer_splash_weekend"),
        ("autumn", 1.10, "harvest_zoo_trail"),
        ("winter", 0.80, "winter_wonderland"),
    ]
    season, visitor_mod, event = rng.choice(seasons)
    payload: Dict = {
        "success": True,
        "season": season,
        "season_visitor_modifier": visitor_mod,
        "special_event": event,
        "summary": f"Season: {season} (visitor x{visitor_mod}, event: {event}).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_event_season_selector(repo_path: str):
    code, payload = run_zoo_event_season_selector(repo_path)
    print(json.dumps(payload))
    return code, payload
