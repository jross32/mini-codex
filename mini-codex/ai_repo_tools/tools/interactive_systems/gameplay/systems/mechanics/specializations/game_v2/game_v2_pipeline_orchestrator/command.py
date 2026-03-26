"""game_v2_pipeline_orchestrator - Compose small builders into a unique CLI adventure game."""

import hashlib
import json
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple

from tools.project_generation.multi_project.structure_generation.filesystem_layouts.directory_materializers.builders.directory_structure_generator.command import (
    run_directory_structure_generator,
)
from tools.project_generation.multi_project.module_generation.python_modules.generic_generators.builders.python_module_generator.command import (
    run_python_module_generator,
)


def _normalized_target_dir(output_dir: str) -> str:
    target = (output_dir or "agent_aish_tests").replace("\\", "/").strip()
    if not target:
        return "../agent_aish_tests"
    if "/" not in target and not target.startswith("."):
        return f"../{target}"
    return target


def _stable_seed(repo_path: str, profile_seed: str) -> int:
    material = f"{repo_path}|{profile_seed or 'default'}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _build_theme(seed_value: int) -> Dict[str, str]:
    rng = random.Random(seed_value)
    archetypes = ["Runepunk", "Ash Desert", "Sky Ruins", "Clockwork Wilds", "Neon Marsh"]
    relics = ["Mirror Key", "Glass Compass", "Star Needle", "Whisper Coin", "Ash Crown"]
    factions = ["Gale Wardens", "Iron Pilgrims", "Velvet Cartel", "Ember Choir", "Null Rangers"]
    title_nouns = ["Frontier", "Vault", "Rift", "Citadel", "Labyrinth"]
    title = f"{rng.choice(archetypes)} {rng.choice(title_nouns)}"
    return {
        "title": title,
        "archetype": rng.choice(archetypes),
        "relic": rng.choice(relics),
        "faction": rng.choice(factions),
    }


def _module_spec(base_dir: str, theme: Dict[str, str], seed_value: int) -> Dict:
    rng = random.Random(seed_value + 17)
    enemy_prefix = rng.choice(["Hollow", "Brass", "Lumen", "Rift", "Sable"])
    enemy_kind = rng.choice(["Stalker", "Warden", "Harrier", "Scavenger", "Oracle"])
    enemy_name = f"{enemy_prefix} {enemy_kind}"

    return {
        "base_dir": base_dir,
        "modules": [
            {
                "path": "game/main.py",
                "docstring": "Entry point for the generated unique adventure game.",
                "imports": [],
                "classes": [],
                "functions": [
                    {
                        "name": "bootstrap",
                        "docstring": "Helper for smoke validation.",
                        "params": [],
                        "code": "return 'ok'",
                    }
                ],
            },
            {
                "path": "game/core/theme.py",
                "docstring": "Theme metadata produced by the small-builder pipeline.",
                "imports": [],
                "classes": [],
                "functions": [
                    {
                        "name": "describe_theme",
                        "docstring": "Return generation metadata.",
                        "params": [],
                        "code": (
                            "return {\n"
                            f"    'title': {theme['title']!r},\n"
                            f"    'archetype': {theme['archetype']!r},\n"
                            f"    'relic': {theme['relic']!r},\n"
                            f"    'faction': {theme['faction']!r},\n"
                            f"    'seed': {seed_value},\n"
                            "}"
                        ),
                    }
                ],
            },
            {
                "path": "game/systems/encounter.py",
                "docstring": "Encounter sampling for generated game variant.",
                "imports": ["import random"],
                "classes": [],
                "functions": [
                    {
                        "name": "roll_encounter",
                        "docstring": "Sample one encounter payload with a coarse threat bias.",
                        "params": ["threat_bias='medium'"],
                        "code": (
                            "threat_pool = ['low', 'medium', 'high']\n"
                            "if threat_bias == 'high':\n"
                            "    threat_pool = ['medium', 'high', 'high']\n"
                            "elif threat_bias == 'low':\n"
                            "    threat_pool = ['low', 'low', 'medium']\n"
                            "enemy = {\n"
                            f"    'name': {enemy_name!r},\n"
                            "    'threat': random.choice(threat_pool),\n"
                            "    'xp_reward': random.randint(8, 16),\n"
                            "    'gold_reward': random.randint(3, 9),\n"
                            "}\n"
                            "return enemy"
                        ),
                    },
                    {
                        "name": "resolve_encounter",
                        "docstring": "Resolve a combat exchange and return outcome data.",
                        "params": ["player", "encounter"],
                        "code": (
                            "difficulty = {'low': 5, 'medium': 8, 'high': 11}[encounter['threat']]\n"
                            "power = player['level'] + player['hp'] // 8\n"
                            "won = power >= difficulty\n"
                            "if not won:\n"
                            "    player['hp'] = max(1, player['hp'] - difficulty)\n"
                            "return {\n"
                            "    'won': won,\n"
                            "    'damage_taken': 0 if won else difficulty,\n"
                            "    'xp_reward': encounter['xp_reward'] if won else encounter['xp_reward'] // 2,\n"
                            "    'gold_reward': encounter['gold_reward'] if won else 0,\n"
                            "}"
                        ),
                    },
                ],
            },
            {
                "path": "game/systems/player.py",
                "docstring": "Player state helpers for generated adventure variants.",
                "imports": [],
                "classes": [],
                "functions": [
                    {
                        "name": "create_player",
                        "docstring": "Create a default player state.",
                        "params": [],
                        "code": (
                            "return {\n"
                            "    'level': 1,\n"
                            "    'xp': 0,\n"
                            "    'gold': 0,\n"
                            "    'hp': 20,\n"
                            "    'inventory': ['field map'],\n"
                            "}"
                        ),
                    },
                    {
                        "name": "rest_player",
                        "docstring": "Recover some HP while preserving upper cap.",
                        "params": ["player"],
                        "code": (
                            "player['hp'] = min(20 + (player['level'] - 1) * 4, player['hp'] + 5)\n"
                            "return player"
                        ),
                    },
                ],
            },
            {
                "path": "game/systems/progression.py",
                "docstring": "Progression and reward logic for generated game variants.",
                "imports": [],
                "classes": [],
                "functions": [
                    {
                        "name": "apply_rewards",
                        "docstring": "Apply rewards and handle level-ups.",
                        "params": ["player", "outcome"],
                        "code": (
                            "player['xp'] += outcome['xp_reward']\n"
                            "player['gold'] += outcome['gold_reward']\n"
                            "threshold = 20 + (player['level'] - 1) * 10\n"
                            "while player['xp'] >= threshold:\n"
                            "    player['xp'] -= threshold\n"
                            "    player['level'] += 1\n"
                            "    player['hp'] += 4\n"
                            "    threshold = 20 + (player['level'] - 1) * 10\n"
                            "return player"
                        ),
                    },
                ],
            },
            {
                "path": "game/systems/narrative.py",
                "docstring": "Narrative helpers for lightweight scene rendering.",
                "imports": [],
                "classes": [],
                "functions": [
                    {
                        "name": "scene_line",
                        "docstring": "Build a short scene line for the current turn.",
                        "params": ["theme", "turn"],
                        "code": (
                            "beats = [\n"
                            "    'wind carries static through broken pylons',\n"
                            "    'a distant bell answers your footsteps',\n"
                            "    'dust glows like embers under moonlight',\n"
                            "]\n"
                            "beat = beats[turn % len(beats)]\n"
                            "return f\"Turn {turn + 1}: In the {theme['archetype']}, {beat}.\""
                        ),
                    }
                ],
            },
        ],
    }


def _rewrite_main_file(main_path: Path) -> None:
    content = (
        "#!/usr/bin/env python3\n"
        "\"\"\"Generated by game_v2_pipeline_orchestrator using small builders.\"\"\"\n"
        "import argparse\n"
        "from core.theme import describe_theme\n"
        "from systems.encounter import roll_encounter, resolve_encounter\n"
        "from systems.narrative import scene_line\n"
        "from systems.player import create_player, rest_player\n"
        "from systems.progression import apply_rewards\n"
        "\n"
        "def _print_header(theme):\n"
        "    print(f\"=== {theme['title']} ===\")\n"
        "    print(f\"Archetype: {theme['archetype']} | Relic: {theme['relic']} | Faction: {theme['faction']}\")\n"
        "    print(f\"Seed: {theme['seed']}\")\n"
        "\n"
        "def preview_turn(theme):\n"
        "    player = create_player()\n"
        "    encounter = roll_encounter('medium')\n"
        "    outcome = resolve_encounter(player, encounter)\n"
        "    apply_rewards(player, outcome)\n"
        "    print(scene_line(theme, 0))\n"
        "    print(f\"Encounter: {encounter['name']} ({encounter['threat']})\")\n"
        "    print(f\"Outcome: {'victory' if outcome['won'] else 'retreat'}\")\n"
        "    print(f\"Level {player['level']} | HP {player['hp']} | XP {player['xp']} | Gold {player['gold']}\")\n"
        "\n"
        "def play_loop(theme):\n"
        "    player = create_player()\n"
        "    turn = 0\n"
        "    print(\"Interactive mode: scout, rest, status, quit\")\n"
        "    while True:\n"
        "        cmd = input('> ').strip().lower()\n"
        "        if cmd in {'quit', 'q', 'exit'}:\n"
        "            print('You leave the frontier for now.')\n"
        "            return\n"
        "        if cmd in {'status', 's'}:\n"
        "            print(f\"Level {player['level']} | HP {player['hp']} | XP {player['xp']} | Gold {player['gold']}\")\n"
        "            continue\n"
        "        if cmd in {'rest', 'r'}:\n"
        "            rest_player(player)\n"
        "            print('You rest and recover composure.')\n"
        "            continue\n"
        "        if cmd not in {'scout', 'explore', 'e'}:\n"
        "            print('Unknown command. Try: scout, rest, status, quit')\n"
        "            continue\n"
        "\n"
        "        encounter = roll_encounter('high' if turn > 1 else 'medium')\n"
        "        outcome = resolve_encounter(player, encounter)\n"
        "        apply_rewards(player, outcome)\n"
        "        print(scene_line(theme, turn))\n"
        "        print(f\"Encounter: {encounter['name']} ({encounter['threat']})\")\n"
        "        print(f\"Outcome: {'victory' if outcome['won'] else 'hard-fought retreat'}\")\n"
        "        print(f\"Level {player['level']} | HP {player['hp']} | XP {player['xp']} | Gold {player['gold']}\")\n"
        "        turn += 1\n"
        "\n"
        "def main(argv=None):\n"
        "    parser = argparse.ArgumentParser(description='Generated adventure game')\n"
        "    parser.add_argument('--play', action='store_true', help='Run interactive loop')\n"
        "    args = parser.parse_args(argv)\n"
        "\n"
        "    theme = describe_theme()\n"
        "    _print_header(theme)\n"
        "    preview_turn(theme)\n"
        "    if args.play:\n"
        "        play_loop(theme)\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
    )
    main_path.write_text(content, encoding="utf-8")


def run_game_v2_pipeline_orchestrator(
    repo_path: str,
    output_dir: str = "agent_aish_tests",
    profile_seed: str = "small-builders-only",
) -> Tuple[int, Dict]:
    t0 = time.monotonic()
    target_dir = _normalized_target_dir(output_dir)
    seed_value = _stable_seed(repo_path, profile_seed)
    theme = _build_theme(seed_value)

    dir_spec = {
        "base": target_dir,
        "dirs": [
            "game",
            "game/core",
            "game/systems",
            "logs",
        ],
        "files": {
            "game/__init__.py": "",
            "game/core/__init__.py": "",
            "game/systems/__init__.py": "",
        },
    }
    _, dir_payload = run_directory_structure_generator(repo_path, spec_json=json.dumps(dir_spec))
    if not dir_payload.get("success"):
        payload = {
            "success": False,
            "summary": "Directory stage failed",
            "stage": "directory_structure_generator",
            "result": dir_payload,
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }
        return 1, payload

    module_spec = _module_spec(target_dir, theme, seed_value)
    _, module_payload = run_python_module_generator(repo_path, module_spec_json=json.dumps(module_spec))
    if not module_payload.get("success"):
        payload = {
            "success": False,
            "summary": "Module stage failed",
            "stage": "python_module_generator",
            "result": module_payload,
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }
        return 1, payload

    main_rel = f"{target_dir}/game/main.py".replace("//", "/")
    main_path = (Path(repo_path) / main_rel).resolve()
    try:
        _rewrite_main_file(main_path)
    except Exception as exc:
        payload = {
            "success": False,
            "summary": "Finalization stage failed",
            "stage": "rewrite_main",
            "error": str(exc),
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
        }
        return 1, payload

    artifacts: List[str] = []
    artifacts.extend(dir_payload.get("files_created", []))
    artifacts.extend(module_payload.get("module_paths", []))

    payload = {
        "success": True,
        "mode": "small_builders_pipeline",
        "gameplay_depth": "preview_plus_interactive_loop",
        "small_builders_used": [
            "directory_structure_generator",
            "python_module_generator",
        ],
        "target_dir": target_dir,
        "entrypoint": main_rel,
        "theme": theme,
        "seed": seed_value,
        "artifacts": artifacts,
        "summary": f"Built unique adventure game at {main_rel} using small builders.",
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
    }
    return 0, payload


def cmd_game_v2_pipeline_orchestrator(
    repo_path: str,
    output_dir: str = None,
    profile_seed: str = None,
):
    code, payload = run_game_v2_pipeline_orchestrator(
        repo_path,
        output_dir=output_dir or "agent_aish_tests",
        profile_seed=profile_seed or "small-builders-only",
    )
    print(json.dumps(payload))
    return code, payload
