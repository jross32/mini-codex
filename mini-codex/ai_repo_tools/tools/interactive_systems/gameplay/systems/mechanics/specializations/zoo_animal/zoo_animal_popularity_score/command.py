"""
zoo_animal_popularity_score - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_animal_popularity_score(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_animal_popularity_score")
    species = rng.choice(["lion","elephant","penguin","gorilla","red_panda","cheetah","flamingo","tiger"])
    base_pop = {"lion":90,"elephant":95,"penguin":85,"gorilla":92,"red_panda":82,"cheetah":78,"flamingo":70,"tiger":93}
    pop = base_pop[species]
    crowd_magnet = pop >= 88
    payload: Dict = {
        "success": True,
        "species": species,
        "popularity": pop,
        "crowd_magnet_flag": crowd_magnet,
        "summary": f"{species} popularity: {pop}/100 (crowd_magnet={crowd_magnet}).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_animal_popularity_score(repo_path: str):
    code, payload = run_zoo_animal_popularity_score(repo_path)
    print(json.dumps(payload))
    return code, payload
