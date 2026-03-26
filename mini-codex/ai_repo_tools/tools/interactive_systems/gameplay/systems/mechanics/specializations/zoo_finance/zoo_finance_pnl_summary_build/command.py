"""
zoo_finance_pnl_summary_build - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_finance_pnl_summary_build(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_finance_pnl_summary_build")
    ticket_rev = round(rng.uniform(3000, 30000), 2)
    food_rev = round(rng.uniform(800, 8000), 2)
    merch_rev = round(rng.uniform(200, 3000), 2)
    animal_exp = round(rng.uniform(2000, 15000), 2)
    staff_exp = round(rng.uniform(3000, 20000), 2)
    util_exp = round(rng.uniform(500, 3000), 2)
    revenue = round(ticket_rev + food_rev + merch_rev, 2)
    expenses = round(animal_exp + staff_exp + util_exp, 2)
    net_pnl = round(revenue - expenses, 2)
    profit_flag = net_pnl > 0
    payload: Dict = {
        "success": True,
        "revenue": revenue,
        "expenses": expenses,
        "net_pnl": net_pnl,
        "profit_flag": profit_flag,
        "breakdown": {
            "ticket_revenue": ticket_rev,
            "food_revenue": food_rev,
            "merch_revenue": merch_rev,
            "animal_upkeep": animal_exp,
            "staff_payroll": staff_exp,
            "utilities": util_exp,
        },
        "summary": f"P&L: rev=${revenue:,.2f}, exp=${expenses:,.2f}, net=${net_pnl:,.2f} ({'PROFIT' if profit_flag else 'LOSS'}).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_finance_pnl_summary_build(repo_path: str):
    code, payload = run_zoo_finance_pnl_summary_build(repo_path)
    print(json.dumps(payload))
    return code, payload
