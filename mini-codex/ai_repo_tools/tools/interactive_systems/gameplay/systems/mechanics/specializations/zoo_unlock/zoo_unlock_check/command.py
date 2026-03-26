"""
zoo_unlock_check - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_unlock_check(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_unlock_check")
    features = [
        ("petting_zoo",        100),
        ("aquarium_wing",      250),
        ("night_safari",       400),
        ("vip_safari_ride",    600),
        ("endangered_program", 800),
        ("world_class_exhibit",1000),
    ]
    feature_name, required = rng.choice(features)
    current_prestige = rng.randint(50, 1200)
    unlocked = current_prestige >= required
    payload: Dict = {
        "success": True,
        "unlocked": unlocked,
        "feature_name": feature_name,
        "required_prestige": required,
        "current_prestige": current_prestige,
        "points_needed": max(0, required - current_prestige),
        "summary": f"Unlock [{feature_name}]: {'UNLOCKED' if unlocked else f'need {required - current_prestige} more prestige'}.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_unlock_check(repo_path: str):
    code, payload = run_zoo_unlock_check(repo_path)
    print(json.dumps(payload))
    return code, payload
