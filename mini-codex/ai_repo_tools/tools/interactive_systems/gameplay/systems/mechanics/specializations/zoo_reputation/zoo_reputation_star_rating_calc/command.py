"""
zoo_reputation_star_rating_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_reputation_star_rating_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_reputation_star_rating_calc")
    avg_happiness = rng.randint(30, 100)
    review_score = round(rng.uniform(2.0, 10.0), 1)
    exhibit_stars = rng.randint(1, 5)
    composite = avg_happiness * 0.4 + review_score * 4 + exhibit_stars * 4
    star_rating = max(1, min(5, round(composite / 20)))
    tier_label = {5:"world_class",4:"excellent",3:"good",2:"average",1:"struggling"}[star_rating]
    payload: Dict = {
        "success": True,
        "star_rating": star_rating,
        "tier_label": tier_label,
        "components": {
            "avg_happiness": avg_happiness,
            "review_score": review_score,
            "exhibit_stars": exhibit_stars,
            "composite": round(composite, 1),
        },
        "summary": f"Zoo rating: {star_rating}★ [{tier_label}] (composite {composite:.1f}).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_reputation_star_rating_calc(repo_path: str):
    code, payload = run_zoo_reputation_star_rating_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
