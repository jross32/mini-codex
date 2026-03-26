"""
zoo_staff_salary_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_staff_salary_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_staff_salary_calc")
    staff_type = rng.choice(["zookeeper","vet","janitor","guide","security"])
    base = {"zookeeper":2400,"vet":4200,"janitor":1800,"guide":2200,"security":2100}[staff_type]
    skill_level = rng.randint(1, 5)
    bonus = round(base * 0.05 * (skill_level - 1), 2)
    salary = round(base + bonus, 2)
    payload: Dict = {
        "success": True,
        "salary": salary,
        "base_salary": base,
        "skill_bonus": bonus,
        "skill_level": skill_level,
        "staff_type": staff_type,
        "summary": f"{staff_type} (skill {skill_level}): ${salary:.2f}/mo.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_staff_salary_calc(repo_path: str):
    code, payload = run_zoo_staff_salary_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
