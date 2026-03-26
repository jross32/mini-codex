"""
zoo_finance_loan_repayment_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple
import math

def run_zoo_finance_loan_repayment_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_finance_loan_repayment_calc")
    import math
    principal = round(rng.uniform(10000, 500000), 2)
    annual_rate = rng.choice([0.04, 0.05, 0.06, 0.07, 0.08])
    term_months = rng.choice([12, 24, 36, 60, 84])
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        payment = principal / term_months
    else:
        payment = principal * (monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)
    payment = round(payment, 2)
    interest_first = round(principal * monthly_rate, 2)
    payload: Dict = {
        "success": True,
        "monthly_payment": payment,
        "principal": principal,
        "interest_portion": interest_first,
        "principal_portion": round(payment - interest_first, 2),
        "annual_rate_pct": round(annual_rate * 100, 1),
        "term_months": term_months,
        "summary": f"Loan repayment: ${payment:.2f}/mo (${principal:,.2f} @ {annual_rate*100:.1f}% over {term_months}mo).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_finance_loan_repayment_calc(repo_path: str):
    code, payload = run_zoo_finance_loan_repayment_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
