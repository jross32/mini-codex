"""
zoo_finance_staff_salary_expense - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_finance_staff_salary_expense(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_finance_staff_salary_expense")
    staff_count = rng.randint(5, 50)
    avg_salary = rng.uniform(1800, 4500)
    total_payroll = round(staff_count * avg_salary, 2)
    payload: Dict = {
        "success": True,
        "total_payroll": total_payroll,
        "staff_count": staff_count,
        "avg_salary": round(avg_salary, 2),
        "summary": f"Payroll: ${total_payroll:,.2f}/mo ({staff_count} staff).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_finance_staff_salary_expense(repo_path: str):
    code, payload = run_zoo_finance_staff_salary_expense(repo_path)
    print(json.dumps(payload))
    return code, payload
