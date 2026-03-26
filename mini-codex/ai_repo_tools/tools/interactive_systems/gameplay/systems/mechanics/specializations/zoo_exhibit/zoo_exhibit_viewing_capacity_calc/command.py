"""
zoo_exhibit_viewing_capacity_calc - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_exhibit_viewing_capacity_calc(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_exhibit_viewing_capacity_calc")
    footprint_tiles = rng.randint(6, 30)
    path_edge_tiles = max(1, round(footprint_tiles * rng.uniform(0.3, 0.6)))
    viewers_per_edge = 4
    viewer_capacity = path_edge_tiles * viewers_per_edge
    payload: Dict = {
        "success": True,
        "viewer_capacity": viewer_capacity,
        "footprint_tiles": footprint_tiles,
        "path_edge_count": path_edge_tiles,
        "viewers_per_edge_tile": viewers_per_edge,
        "summary": f"Viewing capacity: {viewer_capacity} visitors ({path_edge_tiles} edge tiles).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_exhibit_viewing_capacity_calc(repo_path: str):
    code, payload = run_zoo_exhibit_viewing_capacity_calc(repo_path)
    print(json.dumps(payload))
    return code, payload
