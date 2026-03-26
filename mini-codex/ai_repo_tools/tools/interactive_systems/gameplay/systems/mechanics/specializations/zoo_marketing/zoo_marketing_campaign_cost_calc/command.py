"""
zoo_marketing_campaign_cost_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_marketing_campaign_cost_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_marketing_campaign_cost_calc")
    tiers = [("flyer",300,1000),("radio",2500,8000),("tv",12000,40000),("viral",5000,25000)]
    tier, cost_min, cost_max = rng.choice(tiers)
    campaign_cost = round(rng.uniform(cost_min, cost_max), 2)
    reach_estimate = round(campaign_cost * rng.uniform(2.0, 10.0))
    payload: Dict = {
        "success": True,
        "campaign_cost": campaign_cost,
        "tier": tier,
        "reach_estimate": reach_estimate,
        "cost_per_reach": round(campaign_cost / max(reach_estimate, 1), 4),
        "summary": f"Campaign [{tier}]: ${campaign_cost:,.2f}, reach {reach_estimate:,}.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_marketing_campaign_cost_calc(repo_path: str):
    code, payload = run_zoo_marketing_campaign_cost_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
