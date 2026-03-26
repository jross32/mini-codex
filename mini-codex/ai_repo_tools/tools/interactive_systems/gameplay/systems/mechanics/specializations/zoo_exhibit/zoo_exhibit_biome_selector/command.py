"""
zoo_exhibit_biome_selector - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_exhibit_biome_selector(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_exhibit_biome_selector")
    biomes = [
        ("savanna",    "hot_dry",     1.2),
        ("arctic",     "cold",        0.9),
        ("rainforest", "humid_warm",  1.1),
        ("wetland",    "humid_mild",  1.0),
        ("mixed",      "temperate",   0.95),
    ]
    biome, climate, capacity_mod = rng.choice(biomes)
    payload: Dict = {
        "success": True,
        "biome": biome,
        "climate": climate,
        "capacity_modifier": capacity_mod,
        "setup_cost_modifier": round(1.3 - capacity_mod * 0.1, 2),
        "summary": f"Exhibit biome: {biome} ({climate}), capacity mod x{capacity_mod}.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_exhibit_biome_selector(repo_path: str):
    code, payload = run_zoo_exhibit_biome_selector(repo_path)
    print(json.dumps(payload))
    return code, payload
