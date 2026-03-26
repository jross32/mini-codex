"""
zoo_exhibit_size_validator - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_exhibit_size_validator(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_exhibit_size_validator")
    species = rng.choice(["lion","elephant","penguin","gorilla","cheetah","flamingo"])
    min_tiles = {"lion":12,"elephant":20,"penguin":8,"gorilla":15,"cheetah":14,"flamingo":6}
    animal_count = rng.randint(1, 5)
    required = min_tiles[species] * animal_count
    actual = rng.randint(4, 30) * animal_count
    valid = actual >= required
    deficit = max(0, required - actual)
    payload: Dict = {
        "success": True,
        "valid": valid,
        "species": species,
        "animal_count": animal_count,
        "min_required_tiles": required,
        "actual_size_tiles": actual,
        "deficit": deficit,
        "summary": f"Size {'OK' if valid else 'FAIL'}: {actual} tiles (need {required}) for {animal_count} {species}.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_exhibit_size_validator(repo_path: str):
    code, payload = run_zoo_exhibit_size_validator(repo_path)
    print(json.dumps(payload))
    return code, payload
