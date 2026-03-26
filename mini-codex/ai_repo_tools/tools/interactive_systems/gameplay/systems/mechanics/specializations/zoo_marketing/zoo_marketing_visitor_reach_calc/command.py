"""
zoo_marketing_visitor_reach_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_marketing_visitor_reach_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_marketing_visitor_reach_calc")
    campaign_tier = rng.choice(["flyer","radio","tv","viral"])
    efficiency = {"flyer":0.01,"radio":0.05,"tv":0.08,"viral":0.12}[campaign_tier]
    reach = rng.randint(1000, 100000)
    extra_visitors = round(reach * efficiency)
    spend = round(extra_visitors * rng.uniform(5, 20))
    roi = round(spend / max(extra_visitors * 12, 1), 2)  # assuming $12 avg ticket
    payload: Dict = {
        "success": True,
        "extra_visitors": extra_visitors,
        "campaign_tier": campaign_tier,
        "campaign_efficiency": efficiency,
        "estimated_revenue": spend,
        "roi": roi,
        "summary": f"Marketing [{campaign_tier}]: +{extra_visitors:,} visitors, est revenue ${spend:,}.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_marketing_visitor_reach_calc(repo_path: str):
    code, payload = run_zoo_marketing_visitor_reach_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
