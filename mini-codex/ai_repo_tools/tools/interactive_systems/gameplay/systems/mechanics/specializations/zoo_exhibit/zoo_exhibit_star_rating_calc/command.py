"""
zoo_exhibit_star_rating_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_exhibit_star_rating_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_exhibit_star_rating_calc")
    animal_health = rng.randint(30, 100)
    decoration = rng.randint(0, 100)
    capacity_used_pct = rng.randint(50, 120)
    composite = animal_health * 0.45 + decoration * 0.35 + max(0, (100 - capacity_used_pct)) * 0.2
    stars = max(1, min(5, round(composite / 20)))
    payload: Dict = {
        "success": True,
        "star_rating": stars,
        "composite_score": round(composite, 1),
        "dimension_scores": {
            "animal_health": animal_health,
            "decoration": decoration,
            "capacity_used_pct": capacity_used_pct,
        },
        "summary": f"Exhibit rating: {stars}★ (score {composite:.1f}/100).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_exhibit_star_rating_calc(repo_path: str):
    code, payload = run_zoo_exhibit_star_rating_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
