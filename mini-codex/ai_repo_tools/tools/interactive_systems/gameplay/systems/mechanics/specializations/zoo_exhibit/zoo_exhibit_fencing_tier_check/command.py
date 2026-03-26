"""
zoo_exhibit_fencing_tier_check - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_exhibit_fencing_tier_check(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_exhibit_fencing_tier_check")
    danger_levels = {1:"basic",2:"reinforced",3:"electric"}
    danger_level = rng.randint(1, 3)
    fence_tiers = {1:"basic",2:"reinforced",3:"electric"}
    fence_tier_id = rng.randint(1, 3)
    fence_tier = fence_tiers[fence_tier_id]
    safe = fence_tier_id >= danger_level
    breach_risk = 0 if safe else (danger_level - fence_tier_id) * 0.15
    payload: Dict = {
        "success": True,
        "safe": safe,
        "fence_tier": fence_tier,
        "fence_tier_id": fence_tier_id,
        "danger_level": danger_level,
        "breach_risk": round(breach_risk, 2),
        "recommended_fence": fence_tiers[danger_level],
        "summary": f"Fence [{fence_tier}] vs danger {danger_level}: {'SAFE' if safe else f'UNSAFE (breach risk {breach_risk:.0%})'}.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_exhibit_fencing_tier_check(repo_path: str):
    code, payload = run_zoo_exhibit_fencing_tier_check(repo_path)
    print(json.dumps(payload))
    return code, payload
