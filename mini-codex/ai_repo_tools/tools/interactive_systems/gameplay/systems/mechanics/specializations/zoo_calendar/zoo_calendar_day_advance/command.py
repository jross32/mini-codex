"""
zoo_calendar_day_advance - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_calendar_day_advance(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_calendar_day_advance")
    start_day = rng.randint(1, 364)
    new_day = start_day + 1
    month = (new_day - 1) // 30 + 1
    month_day = (new_day - 1) % 30 + 1
    seasons = {1:"winter",2:"winter",3:"spring",4:"spring",5:"spring",6:"summer",
               7:"summer",8:"summer",9:"autumn",10:"autumn",11:"autumn",12:"winter"}
    season = seasons[min(month, 12)]
    weekend_flag = new_day % 7 in (6, 0)
    payload: Dict = {
        "success": True,
        "day": new_day,
        "month": month,
        "month_day": month_day,
        "season": season,
        "weekend_flag": weekend_flag,
        "summary": f"Day {new_day}: month {month}, day {month_day} ({season}){' [WEEKEND]' if weekend_flag else ''}.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_calendar_day_advance(repo_path: str):
    code, payload = run_zoo_calendar_day_advance(repo_path)
    print(json.dumps(payload))
    return code, payload
