"""
zoo_animal_biome_match_check - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_animal_biome_match_check(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_animal_biome_match_check")
    species_biome = {"lion":"savanna","elephant":"savanna","penguin":"arctic","gorilla":"rainforest",
                     "polar_bear":"arctic","red_panda":"rainforest","flamingo":"wetland","tiger":"rainforest"}
    species = rng.choice(list(species_biome.keys()))
    exhibit_biome = rng.choice(["savanna","arctic","rainforest","wetland","mixed"])
    natural_biome = species_biome[species]
    compatible = exhibit_biome == natural_biome or exhibit_biome == "mixed"
    penalty_flag = not compatible
    payload: Dict = {
        "success": True,
        "compatible": compatible,
        "species": species,
        "species_biome": natural_biome,
        "exhibit_biome": exhibit_biome,
        "penalty_flag": penalty_flag,
        "summary": f"Biome check: {species} in {exhibit_biome} — {'compatible' if compatible else 'MISMATCH (penalty)'}.",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_animal_biome_match_check(repo_path: str):
    code, payload = run_zoo_animal_biome_match_check(repo_path)
    print(json.dumps(payload))
    return code, payload
