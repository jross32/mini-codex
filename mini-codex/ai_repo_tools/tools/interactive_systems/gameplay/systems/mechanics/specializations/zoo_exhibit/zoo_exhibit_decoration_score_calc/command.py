"""
zoo_exhibit_decoration_score_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_exhibit_decoration_score_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_exhibit_decoration_score_calc")
    flora_count = rng.randint(0, 15)
    item_count = rng.randint(0, 10)
    score = min(100, flora_count * 4 + item_count * 5)
    if score >= 80:
        tier = "lush"
    elif score >= 50:
        tier = "decorated"
    elif score >= 20:
        tier = "basic"
    else:
        tier = "bare"
    payload: Dict = {
        "success": True,
        "decoration_score": score,
        "flora_count": flora_count,
        "item_count": item_count,
        "tier": tier,
        "summary": f"Decoration: {score}/100 ({tier}) — {flora_count} flora, {item_count} items.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_exhibit_decoration_score_calc(repo_path: str):
    code, payload = run_zoo_exhibit_decoration_score_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
