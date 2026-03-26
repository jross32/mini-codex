"""
cyberpunk_bar_sim_game_builder - Build a playable cyberpunk bar management simulation game from generated engine scaffold.

Category: game_systems
Returns: success, summary, elapsed_ms

NOTE: This tool was scaffolded by toolmaker. Implement run_cyberpunk_bar_sim_game_builder() logic.
"""
import json
import time
from pathlib import Path
from typing import Dict, Tuple

from tools.project_generation.multi_project.engine_building.mode_builders.cyberpunk.simulation_projects.cyberpunk_sim_builder.command import (
    run_cyberpunk_sim_builder,
)


def _write(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    prior = path.read_text(encoding="utf-8") if path.exists() else None
    if prior == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def run_cyberpunk_bar_sim_game_builder(repo_path: str) -> Tuple[int, Dict]:
    """
    Build a playable cyberpunk bar management simulation game from generated engine scaffold.

    Returns: success, summary, elapsed_ms
    """
    t0 = time.monotonic()

    root = Path(repo_path)
    project_root = root / "aish_tests" / "multi_game_projects" / "cyberpunk_bar_management_sim"

    scaffold_payload = None
    if not project_root.is_dir():
        build_code, scaffold_payload = run_cyberpunk_sim_builder(repo_path)
        if build_code != 0:
            payload: Dict = {
                "success": False,
                "error": "scaffold_generation_failed",
                "build": scaffold_payload,
                "summary": "Could not create cyberpunk scaffold before game build.",
                "elapsed_ms": round((time.monotonic() - t0) * 1000),
            }
            return 2, payload

    changed = []

    engine_py = project_root / "core" / "engine.py"
    entity_py = project_root / "entities" / "entity.py"
    sim_py = project_root / "systems" / "bar" / "simulation.py"
    main_py = project_root / "main.py"
    readme_md = project_root / "README.md"

    engine_content = '''"""Engine runtime for the cyberpunk bar simulation."""

from dataclasses import dataclass


@dataclass
class Engine:
    mode: str = "cyberpunk_bar"
    tick: int = 0

    def next_tick(self) -> int:
        self.tick += 1
        return self.tick

    def run(self) -> None:
        print(f"Running {self.mode} engine at tick {self.tick}")
'''

    entity_content = '''"""Generic entity model reused by all game types."""


class Entity:
    """Universal entity."""

    def __init__(self, entity_id, name, stats):
        self.entity_id = entity_id
        self.name = name
        self.stats = stats

    def get_stat(self, key, default=0):
        return self.stats.get(key, default)
'''

    sim_content = '''"""Core cyberpunk bar simulation logic."""

from dataclasses import dataclass
from random import Random


@dataclass
class BarState:
    day: int = 1
    cash: int = 1200
    stock: int = 45
    reputation: int = 30
    stress: int = 10


def run_shift(state: BarState, action: str, rng: Random) -> dict:
    crowd = rng.randint(18, 42)
    demand = crowd + (state.reputation // 5)
    served = min(demand, state.stock)
    income = served * rng.randint(14, 24)

    state.stock -= served
    state.cash += income

    if action == "import_stock":
        buy = 24
        cost = buy * 8
        if state.cash >= cost:
            state.cash -= cost
            state.stock += buy
            state.reputation += 1
    elif action == "street_promo":
        state.cash = max(0, state.cash - 120)
        state.reputation += 3
        state.stress += 2
    elif action == "tight_security":
        state.cash = max(0, state.cash - 80)
        state.stress = max(0, state.stress - 2)
    else:
        state.stress += 1

    if state.stock < 10:
        state.reputation -= 2
        state.stress += 3

    state.reputation = max(0, min(100, state.reputation))
    state.stress = max(0, min(100, state.stress))

    report = {
        "day": state.day,
        "crowd": crowd,
        "served": served,
        "cash": state.cash,
        "stock": state.stock,
        "reputation": state.reputation,
        "stress": state.stress,
        "action": action,
    }
    state.day += 1
    return report


def score(state: BarState) -> int:
    return state.cash + (state.reputation * 25) - (state.stress * 15)
'''

    main_content = '''from random import Random

from core.engine import Engine
from systems.bar.simulation import BarState, run_shift, score


def choose_action(day: int) -> str:
    cycle = ["import_stock", "street_promo", "tight_security", "hold"]
    return cycle[(day - 1) % len(cycle)]


def run_game(days: int = 7) -> dict:
    engine = Engine()
    rng = Random(2077)
    state = BarState()

    print("=== CYBERPUNK BAR MANAGEMENT SIM ===")
    for _ in range(days):
        action = choose_action(state.day)
        report = run_shift(state, action, rng)
        engine.next_tick()
        print(
            f"Day {report['day']}: action={report['action']} crowd={report['crowd']} "
            f"served={report['served']} cash={report['cash']} stock={report['stock']} "
            f"rep={report['reputation']} stress={report['stress']}"
        )

    final_score = score(state)
    print(f"Final score: {final_score}")
    return {"days": days, "cash": state.cash, "stock": state.stock, "reputation": state.reputation, "stress": state.stress, "score": final_score}


if __name__ == "__main__":
    run_game()
'''

    readme_content = '''# cyberpunk_bar_management_sim

Game Type: cyberpunk
Theme: neon-noir

System folders:
- core/
- ui/
- entities/
- systems/

## Play

Run:

python main.py

The game simulates a 7-day bar management run with deterministic neon-noir events and prints a final score.
'''

    for p, content in [
        (engine_py, engine_content),
        (entity_py, entity_content),
        (sim_py, sim_content),
        (main_py, main_content),
        (readme_md, readme_content),
    ]:
        if _write(p, content):
            changed.append(str(p.relative_to(root)))

    payload: Dict = {
        "success": True,
        "cyberpunk_bar_sim_game_builder_mode": "build_playable_game",
        "project_root": str(project_root.relative_to(root)),
        "files_changed": changed,
        "scaffold_built": scaffold_payload is not None,
        "summary": "Built playable cyberpunk bar management simulation game.",
    }

    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_cyberpunk_bar_sim_game_builder(repo_path: str):
    code, payload = run_cyberpunk_bar_sim_game_builder(repo_path)
    print(json.dumps(payload))
    return code, payload
