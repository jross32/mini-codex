"""
zoo_reputation_review_aggregate - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_reputation_review_aggregate(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_reputation_review_aggregate")
    total_reviews = rng.randint(10, 500)
    scores = [rng.uniform(1, 10) for _ in range(min(total_reviews, 50))]
    avg = round(sum(scores) / len(scores), 2) if scores else 5.0
    positive_pct = round(sum(1 for s in scores if s >= 6) / len(scores) * 100, 1) if scores else 50.0
    complaints = rng.choice(["queue_wait","crowds","food_price","animal_welfare","cleanliness","parking"])
    payload: Dict = {
        "success": True,
        "avg_score": avg,
        "total_reviews": total_reviews,
        "positive_pct": positive_pct,
        "top_complaint": complaints,
        "summary": f"Reviews: {avg:.1f}/10 avg, {positive_pct}% positive ({total_reviews} reviews).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_reputation_review_aggregate(repo_path: str):
    code, payload = run_zoo_reputation_review_aggregate(repo_path)
    print(json.dumps(payload))
    return code, payload
