"""
zoo_animal_species_selector - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_animal_species_selector(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_animal_species_selector")
    catalogue = [
        ("lion",      "savanna",  "rare",   3, 90),
        ("elephant",  "savanna",  "rare",   2, 95),
        ("giraffe",   "savanna",  "common", 1, 80),
        ("penguin",   "arctic",   "common", 1, 85),
        ("polar_bear","arctic",   "rare",   3, 88),
        ("gorilla",   "rainforest","rare",  2, 92),
        ("red_panda", "rainforest","uncommon",1,82),
        ("cheetah",   "savanna",  "uncommon",2,78),
        ("flamingo",  "wetland",  "common", 1, 70),
        ("crocodile", "wetland",  "common", 2, 65),
        ("tiger",     "rainforest","rare",  3, 93),
        ("koala",     "rainforest","uncommon",1,88),
    ]
    species, biome, rarity, danger_level, popularity = rng.choice(catalogue)
    payload: Dict = {
        "success": True,
        "species": species,
        "biome": biome,
        "rarity": rarity,
        "danger_level": danger_level,
        "popularity": popularity,
        "summary": f"Selected: {species} (biome={biome}, rarity={rarity}, danger={danger_level}).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_animal_species_selector(repo_path: str):
    code, payload = run_zoo_animal_species_selector(repo_path)
    print(json.dumps(payload))
    return code, payload
