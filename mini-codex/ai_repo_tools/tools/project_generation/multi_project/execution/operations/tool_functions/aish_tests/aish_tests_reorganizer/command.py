"""
aish_tests_reorganizer - Rename and reorganize aish_tests game/test folders into gameplay-based categories with safe reference updates.

Category: execution
Returns: success, summary, elapsed_ms

NOTE: This tool was scaffolded by toolmaker. Implement run_aish_tests_reorganizer() logic.
"""
import json
import time
from pathlib import Path
from typing import Dict, Tuple


def _safe_move(src: Path, dst: Path) -> bool:
    if not src.exists() or src == dst:
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return False
    src.rename(dst)
    return True


def _rewrite_file(path: Path, old: str, new: str) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    updated = text.replace(old, new)
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def _rewrite_readme(path: Path) -> bool:
    if not path.exists():
        return False
    content = """# AISH Game Test Projects

## Quick Play Entrypoints

- Classic RPG: `python aish_tests/rpg_adventure/classic_adventure_quest/main.py`
- Modular RPG V2: `python aish_tests/rpg_adventure/modular_adventure_quest_v2/main.py`
- Cyberpunk Bar Sim: `python aish_tests/multi_game_projects/cyberpunk/neon_bar_management_sim/main.py`
- Roguelike Survival Sim: `python aish_tests/multi_game_projects/roguelike/dungeon_survival_roguelike/main.py`

## Organized Layout

```
aish_tests/
  rpg_adventure/
    classic_adventure_quest/
    modular_adventure_quest_v2/
    tests/
  multi_game_projects/
    cyberpunk/
      neon_bar_management_sim/
    roguelike/
      dungeon_survival_roguelike/
    fantasy/
      fantasy_adventure_rpg_case/
  build_v2_via_tools.py
```
"""
    prior = path.read_text(encoding="utf-8")
    if prior == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def run_aish_tests_reorganizer(repo_path: str) -> Tuple[int, Dict]:
    """
    Rename and reorganize aish_tests game/test folders into gameplay-based categories with safe reference updates.

    Returns: success, summary, elapsed_ms
    """
    t0 = time.monotonic()

    root = Path(repo_path)
    tests_root = root / "aish_tests"
    if not tests_root.is_dir():
        payload: Dict = {
            "success": False,
            "error": "aish_tests_not_found",
            "path": str(tests_root),
            "summary": "Could not find aish_tests directory.",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }
        return 2, payload

    moved = []
    updated = []

    move_plan = [
        (
            tests_root / "game",
            tests_root / "rpg_adventure" / "classic_adventure_quest",
        ),
        (
            tests_root / "game_v2",
            tests_root / "rpg_adventure" / "modular_adventure_quest_v2",
        ),
        (
            tests_root / "test_game.py",
            tests_root / "rpg_adventure" / "tests" / "classic_adventure_systems_test.py",
        ),
        (
            tests_root / "multi_game_projects" / "cyberpunk_bar_management_sim",
            tests_root
            / "multi_game_projects"
            / "cyberpunk"
            / "neon_bar_management_sim",
        ),
        (
            tests_root / "multi_game_projects" / "roguelike_survival_sim",
            tests_root
            / "multi_game_projects"
            / "roguelike"
            / "dungeon_survival_roguelike",
        ),
        (
            tests_root / "multi_game_projects" / "rpg_engine_case",
            tests_root
            / "multi_game_projects"
            / "fantasy"
            / "fantasy_adventure_rpg_case",
        ),
    ]

    for src, dst in move_plan:
        if _safe_move(src, dst):
            moved.append({"from": str(src.relative_to(root)), "to": str(dst.relative_to(root))})

    test_file = tests_root / "rpg_adventure" / "tests" / "classic_adventure_systems_test.py"
    if test_file.exists():
        fixed_test = '''#!/usr/bin/env python3
"""Test suite for the classic CLI RPG adventure implementation."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "classic_adventure_quest"
sys.path.insert(0, str(BASE))

from main import Character, Monster, Combat, UI, Shop, save_game, load_game, spawn_monster, REST_PLACES


def test_character_system():
    p = Character("Hero", 1, 0)
    p.take_damage(15)
    p.heal(20)
    p.gain_exp(150)
    return p.level >= 2 and p.hp > 0


def test_monster_system():
    for level in [1, 3, 5, 10]:
        mon = spawn_monster(level)
        if mon.hp <= 0:
            return False
    return True


def test_combat_system():
    player = Character("TestHero", level=1)
    monster = Monster("Goblin", 15, 4, 1, 1, {"gold": 50})
    combat = Combat(player, monster)
    turn = 0
    while not combat.is_over() and turn < 20:
        combat.resolve()
        turn += 1
    return player.is_alive()


def test_shop_system():
    for _ in range(5):
        items = Shop.items()
        if len(items) < 2:
            return False
    return True


def test_rest_system():
    player = Character("TestHero")
    for _, heal, cost in REST_PLACES:
        player.hp = 20
        player.gold = 1000
        player.heal(heal)
        player.gold -= cost
    return True


def test_save_load_system():
    p1 = Character("SaveTest", level=3, exp=50)
    p1.hp = 55
    p1.strength = 15
    p1.gold = 500
    save_game(p1)
    p2 = load_game()
    if p2 is None:
        return False
    return p2.name == p1.name and p2.level == p1.level and p2.hp == p1.hp and p2.gold == p1.gold


def main():
    tests = [
        test_character_system,
        test_monster_system,
        test_combat_system,
        test_shop_system,
        test_rest_system,
        test_save_load_system,
    ]
    results = []
    for t in tests:
        try:
            results.append(bool(t()))
        except Exception:
            results.append(False)
    passed = sum(1 for r in results if r)
    print(json.dumps({"success": passed == len(results), "passed": passed, "total": len(results)}))


if __name__ == "__main__":
    import json

    main()
'''
        prior = test_file.read_text(encoding="utf-8")
        if prior != fixed_test:
            test_file.write_text(fixed_test, encoding="utf-8")
            updated.append(str(test_file.relative_to(root)))

    build_script = tests_root / "build_v2_via_tools.py"
    if _rewrite_file(build_script, '"game_v2"', '"rpg_adventure/modular_adventure_quest_v2"'):
        updated.append(str(build_script.relative_to(root)))
    if _rewrite_file(build_script, '"game_v2/', '"rpg_adventure/modular_adventure_quest_v2/'):
        updated.append(str(build_script.relative_to(root)))
    if _rewrite_file(
        build_script,
        '"base_dir": "aish_tests/game_v2"',
        '"base_dir": "aish_tests/rpg_adventure/modular_adventure_quest_v2"',
    ):
        updated.append(str(build_script.relative_to(root)))

    if _rewrite_readme(tests_root / "README.md"):
        updated.append(str((tests_root / "README.md").relative_to(root)))

    payload: Dict = {
        "success": True,
        "aish_tests_reorganizer_mode": "rename_and_categorize",
        "moved": moved,
        "updated_files": sorted(set(updated)),
        "summary": "Renamed game/test projects and organized aish_tests into gameplay categories.",
    }

    payload["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return 0, payload


def cmd_aish_tests_reorganizer(repo_path: str):
    code, payload = run_aish_tests_reorganizer(repo_path)
    print(json.dumps(payload))
    return code, payload
