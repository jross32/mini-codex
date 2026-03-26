"""
zoo_visitor_happiness_animal_bonus - auto-implemented by _zoo_impl_batch.py
"""
import json
import random
import time
from typing import Dict, Tuple


def run_zoo_visitor_happiness_animal_bonus(repo_path: str) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    rng = random.Random("zoo_visitor_happiness_animal_bonus")
    species = rng.choice(["lion","elephant","giraffe","penguin","red_panda","gorilla","cheetah","flamingo"])
    behaviors = {"active":15,"feeding":20,"sleeping":5,"playing":18,"bathing":12}
    behavior_state = rng.choice(list(behaviors.keys()))
    bonus = behaviors[behavior_state]
    payload: Dict = {
        "success": True,
        "bonus": bonus,
        "animal_name": species,
        "behavior_state": behavior_state,
        "summary": f"+{bonus} happiness watching {species} ({behavior_state}).",
    }
    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_zoo_visitor_happiness_animal_bonus(repo_path: str):
    code, payload = run_zoo_visitor_happiness_animal_bonus(repo_path)
    print(json.dumps(payload))
    return code, payload
