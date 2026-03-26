#!/usr/bin/env python3
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
