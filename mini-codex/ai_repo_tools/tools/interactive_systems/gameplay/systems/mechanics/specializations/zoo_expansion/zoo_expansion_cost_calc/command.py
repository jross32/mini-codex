"""
zoo_expansion_cost_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_expansion_cost_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_expansion_cost_calc")
    current_size_tiles = rng.randint(50, 500)
    direction = rng.choice(["north","south","east","west"])
    tiles_to_add = rng.randint(10, 80)
    base_per_tile = rng.uniform(800, 2500)
    size_premium = 1 + (current_size_tiles / 500) * 0.5
    expansion_cost = round(tiles_to_add * base_per_tile * size_premium, 2)
    new_size = current_size_tiles + tiles_to_add
    payload: Dict = {
        "success": True,
        "expansion_cost": expansion_cost,
        "direction": direction,
        "tiles_added": tiles_to_add,
        "current_size": current_size_tiles,
        "new_size": new_size,
        "cost_per_tile": round(expansion_cost / tiles_to_add, 2),
        "summary": f"Expansion [{direction}]: ${expansion_cost:,.2f} for {tiles_to_add} tiles → {new_size} total.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_expansion_cost_calc(repo_path: str):
    code, payload = run_zoo_expansion_cost_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
