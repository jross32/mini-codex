"""
zoo_finance_ticket_revenue_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_finance_ticket_revenue_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_finance_ticket_revenue_calc")
    visitor_count = rng.randint(100, 2000)
    adult_pct = rng.uniform(0.55, 0.75)
    child_pct = 1 - adult_pct
    adult_price = round(rng.uniform(12.0, 22.0), 2)
    child_price = round(adult_price * 0.5, 2)
    adults = round(visitor_count * adult_pct)
    children = visitor_count - adults
    revenue = round(adults * adult_price + children * child_price, 2)
    avg_ticket = round(revenue / max(visitor_count, 1), 2)
    payload: Dict = {
        "success": True,
        "revenue": revenue,
        "visitor_count": visitor_count,
        "adults": adults,
        "children": children,
        "adult_price": adult_price,
        "child_price": child_price,
        "avg_ticket_price": avg_ticket,
        "summary": f"Ticket revenue: ${revenue:,.2f} ({visitor_count} visitors).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_finance_ticket_revenue_calc(repo_path: str):
    code, payload = run_zoo_finance_ticket_revenue_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
