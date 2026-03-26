"""
zoo_visitor_review_score_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_visitor_review_score_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_visitor_review_score_calc")
    happiness = rng.randint(20, 100)
    spend_satisfaction = rng.uniform(0.5, 1.0)
    score = round((happiness * 0.7 + spend_satisfaction * 30), 1)
    score = max(1.0, min(10.0, score / 10))
    stars = max(1, min(5, round(score / 2)))
    if score >= 8.0:
        verdict = "excellent"
    elif score >= 6.0:
        verdict = "good"
    elif score >= 4.0:
        verdict = "average"
    else:
        verdict = "poor"
    payload: Dict = {
        "success": True,
        "review_score": round(score, 1),
        "stars": stars,
        "happiness_input": happiness,
        "verdict": verdict,
        "summary": f"Review: {score:.1f}/10 ({stars}★) - {verdict}.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_visitor_review_score_calc(repo_path: str):
    code, payload = run_zoo_visitor_review_score_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
