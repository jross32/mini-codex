import json
import subprocess
import sys


def run_aish_tool(tool_name, *args):
    cmd = [sys.executable, "-m", "aish", "tool", tool_name, "--repo", ".", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise SystemExit(result.returncode)


def main():
    dir_spec = {
        "base": "aish_tests",
        "dirs": [
            "rpg_adventure/modular_adventure_quest_v2",
            "rpg_adventure/modular_adventure_quest_v2/core",
            "rpg_adventure/modular_adventure_quest_v2/entities",
            "rpg_adventure/modular_adventure_quest_v2/systems",
            "rpg_adventure/modular_adventure_quest_v2/ui",
            "rpg_adventure/modular_adventure_quest_v2/data"
        ],
        "files": {
            "rpg_adventure/modular_adventure_quest_v2/__init__.py": "",
            "rpg_adventure/modular_adventure_quest_v2/data/.gitkeep": ""
        }
    }
    run_aish_tool("directory_structure_generator", json.dumps(dir_spec))

    module_spec = {
        "base_dir": "aish_tests/rpg_adventure/modular_adventure_quest_v2",
        "modules": [
            {
                "path": "entities/character.py",
                "docstring": "V2 character functions",
                "imports": [],
                "functions": [
                    {
                        "name": "new_character",
                        "params": ["name"],
                        "code": "return {'name': name, 'level': 1, 'exp': 0, 'hp': 120, 'max_hp': 120, 'strength': 12, 'defense': 4, 'gold': 100, 'inventory': []}"
                    },
                    {
                        "name": "character_take_damage",
                        "params": ["player", "dmg"],
                        "code": "final = max(1, dmg - player['defense'] // 2)\nplayer['hp'] = max(0, player['hp'] - final)\nreturn final"
                    },
                    {
                        "name": "character_heal",
                        "params": ["player", "amt"],
                        "code": "player['hp'] = min(player['max_hp'], player['hp'] + amt)\nreturn player['hp']"
                    },
                    {
                        "name": "character_gain_exp",
                        "params": ["player", "amt"],
                        "code": "player['exp'] += amt\nneed = player['level'] * 100\nif player['exp'] >= need:\n    player['exp'] -= need\n    player['level'] += 1\n    player['max_hp'] += 20\n    player['hp'] = player['max_hp']\n    player['strength'] += 2\n    player['defense'] += 1\n    return True\nreturn False"
                    },
                    {
                        "name": "character_is_alive",
                        "params": ["player"],
                        "code": "return player['hp'] > 0"
                    }
                ]
            },
            {
                "path": "entities/monster.py",
                "docstring": "V2 monster functions",
                "imports": [],
                "functions": [
                    {
                        "name": "spawn_monster",
                        "params": ["level"],
                        "code": "base=[{'name':'Goblin','hp':25,'atk':7,'def':2,'gold':70},{'name':'Orc','hp':45,'atk':10,'def':3,'gold':130},{'name':'Troll','hp':75,'atk':14,'def':4,'gold':220},{'name':'Dragon','hp':140,'atk':20,'def':7,'gold':700}]\nidx=min(max(0,level-1),len(base)-1)\nm=dict(base[idx])\nm['hp'] += level*6\nm['max_hp'] = m['hp']\nreturn m"
                    },
                    {
                        "name": "monster_is_alive",
                        "params": ["monster"],
                        "code": "return monster['hp'] > 0"
                    }
                ]
            },
            {
                "path": "systems/combat.py",
                "docstring": "V2 combat functions",
                "imports": [
                    "import random",
                    "from entities.character import character_take_damage",
                    "from entities.monster import monster_is_alive"
                ],
                "functions": [
                    {
                        "name": "player_attack",
                        "params": ["player", "monster"],
                        "code": "raw = player['strength'] + random.randint(1,6)\ndmg = max(1, raw - monster['def'])\nmonster['hp'] = max(0, monster['hp'] - dmg)\nreturn dmg"
                    },
                    {
                        "name": "enemy_attack",
                        "params": ["player", "monster"],
                        "code": "raw = monster['atk'] + random.randint(0,4)\nreturn character_take_damage(player, raw)"
                    },
                    {
                        "name": "combat_round",
                        "params": ["player", "monster"],
                        "code": "p = player_attack(player, monster)\nm = 0\nif monster_is_alive(monster):\n    m = enemy_attack(player, monster)\nreturn {'player_damage': p, 'enemy_damage': m}"
                    }
                ]
            },
            {
                "path": "systems/shops.py",
                "docstring": "V2 branching shop functions",
                "imports": ["import random"],
                "functions": [
                    {
                        "name": "shop_catalogs",
                        "params": [],
                        "code": "return {'blacksmith':[('Iron Sword',120),('Steel Shield',140)],'apothecary':[('Potion',60),('Mega Potion',180)],'arcane':[('Rune Stone',220),('Mana Draught',130)],'general':[('Rope',20),('Torch',15)],'night_market':[('Shadow Dagger',360),('Cursed Charm',420)]}"
                    },
                    {
                        "name": "choose_shop_type",
                        "params": [],
                        "code": "types=['blacksmith','apothecary','arcane','general']\nif random.random() < 0.15:\n    return 'night_market'\nreturn random.choice(types)"
                    },
                    {
                        "name": "rare_trader_event",
                        "params": [],
                        "code": "if random.random() < 0.1:\n    return {'name':'Wandering Relic Broker','items':[('Phoenix Blade',900),('Ancient Aegis',1100)]}\nreturn None"
                    },
                    {
                        "name": "apply_purchase",
                        "params": ["player", "item", "price"],
                        "code": "if player['gold'] < price:\n    return False\nplayer['gold'] -= price\nplayer['inventory'].append(item)\nreturn True"
                    }
                ]
            },
            {
                "path": "systems/rest.py",
                "docstring": "V2 rest functions",
                "imports": [],
                "functions": [
                    {
                        "name": "rest_locations",
                        "params": [],
                        "code": "return [('Inn',80,60),('Shrine',120,110),('Temple',180,210)]"
                    },
                    {
                        "name": "apply_rest",
                        "params": ["player", "choice_index"],
                        "code": "spots=rest_locations()\nif choice_index < 0 or choice_index >= len(spots):\n    return {'ok': False, 'reason': 'invalid'}\nname, heal, cost = spots[choice_index]\nif player['gold'] < cost:\n    return {'ok': False, 'reason': 'gold'}\nplayer['gold'] -= cost\nplayer['hp'] = min(player['max_hp'], player['hp'] + heal)\nreturn {'ok': True, 'name': name, 'heal': heal, 'cost': cost}"
                    }
                ]
            },
            {
                "path": "core/save_load.py",
                "docstring": "V2 save/load functions",
                "imports": ["import json", "from pathlib import Path"],
                "functions": [
                    {
                        "name": "save_game",
                        "params": ["player", "save_path"],
                        "code": "p = Path(save_path)\np.parent.mkdir(exist_ok=True)\np.write_text(json.dumps(player), encoding='utf-8')\nreturn True"
                    },
                    {
                        "name": "load_game",
                        "params": ["save_path"],
                        "code": "p = Path(save_path)\nif not p.exists():\n    return None\nreturn json.loads(p.read_text(encoding='utf-8'))"
                    }
                ]
            },
            {
                "path": "ui/terminal_ui.py",
                "docstring": "V2 terminal ui functions",
                "imports": ["import sys", "import time"],
                "functions": [
                    {
                        "name": "clear_screen",
                        "params": [],
                        "code": "print(chr(27) + '[2J' + chr(27) + '[H')"
                    },
                    {
                        "name": "loading_bar",
                        "params": ["msg"],
                        "code": "for i in range(0,101,5):\n    filled=i//5\n    bar='#'*filled + '-'*(20-filled)\n    sys.stdout.write(f'\\r{msg}: [{bar}] {i}%')\n    sys.stdout.flush()\n    time.sleep(0.01)\nprint()"
                    },
                    {
                        "name": "title_banner",
                        "params": ["text"],
                        "code": "print()\nprint(text.center(80))\nprint()"
                    },
                    {
                        "name": "print_status",
                        "params": ["player"],
                        "code": "print(f\"LVL {player['level']} | HP {player['hp']}/{player['max_hp']} | EXP {player['exp']}/{player['level']*100} | GOLD {player['gold']}\")"
                    }
                ]
            },
            {
                "path": "main.py",
                "docstring": "V2 main game loop",
                "imports": [
                    "from entities.character import new_character, character_is_alive, character_gain_exp",
                    "from entities.monster import spawn_monster, monster_is_alive",
                    "from systems.combat import combat_round",
                    "from systems.shops import shop_catalogs, choose_shop_type, rare_trader_event, apply_purchase",
                    "from systems.rest import rest_locations, apply_rest",
                    "from core.save_load import save_game, load_game",
                    "from ui.terminal_ui import clear_screen, loading_bar, title_banner, print_status"
                ],
                "functions": [
                    {
                        "name": "explore",
                        "params": ["player"],
                        "code": "monster = spawn_monster(player['level'])\nprint(f\"A wild {monster['name']} appears!\")\nwhile character_is_alive(player) and monster_is_alive(monster):\n    print(f\"Monster HP: {monster['hp']}\")\n    action=input('1.Attack 2.Run >> ').strip()\n    if action=='2':\n        print('You escaped.')\n        return\n    r = combat_round(player, monster)\n    print(f\"You dealt {r['player_damage']}; enemy dealt {r['enemy_damage']}.\")\nif character_is_alive(player):\n    print('Victory!')\n    player['gold'] += monster['gold']\n    leveled = character_gain_exp(player, monster['gold'])\n    if leveled:\n        print('Level up!')\nelse:\n    print('You fell in battle, but are revived at town.')\n    player['hp'] = player['max_hp']"
                    },
                    {
                        "name": "shop_menu",
                        "params": ["player"],
                        "code": "catalogs = shop_catalogs()\nstype = choose_shop_type()\nprint(f\"Shop type: {stype}\")\nitems = catalogs[stype]\nfor i,(n,p) in enumerate(items,1):\n    print(f\"{i}. {n} - {p}g\")\nrare = rare_trader_event()\nif rare:\n    print(f\"Rare trader: {rare['name']}\")\nidx = int(input('Buy index (0 skip): ') or '0')\nif idx > 0 and idx <= len(items):\n    n,p = items[idx-1]\n    if apply_purchase(player,n,p):\n        print(f\"Bought {n}\")\n    else:\n        print('Not enough gold')"
                    },
                    {
                        "name": "rest_menu",
                        "params": ["player"],
                        "code": "spots = rest_locations()\nfor i,(n,h,c) in enumerate(spots,1):\n    print(f\"{i}. {n} heal {h} cost {c}\")\nidx = int(input('Choice (0 cancel): ') or '0') - 1\nif idx >= 0:\n    out = apply_rest(player, idx)\n    if out['ok']:\n        print(f\"Rested at {out['name']}\")\n    else:\n        print('Rest failed')"
                    },
                    {
                        "name": "game_loop",
                        "params": ["player", "save_path"],
                        "code": "while True:\n    clear_screen()\n    print_status(player)\n    print('\\n1.Explore 2.Shop 3.Rest 4.Save 5.Quit')\n    c=input('>> ').strip()\n    if c=='1':\n        explore(player)\n    elif c=='2':\n        shop_menu(player)\n    elif c=='3':\n        rest_menu(player)\n    elif c=='4':\n        save_game(player, save_path)\n        print('Saved.')\n    elif c=='5':\n        return"
                    },
                    {
                        "name": "main",
                        "params": [],
                        "code": "save_path = 'aish_tests/save_v2.json'\nclear_screen()\nloading_bar('Loading V2')\ntitle_banner('=== ADVENTURE QUEST V2 ===')\nprint('1. New Game\\n2. Load Game\\n3. Exit')\nc=input('>> ').strip()\nif c == '1':\n    name=input('Name: ').strip() or 'HeroV2'\n    player=new_character(name)\n    game_loop(player, save_path)\nelif c == '2':\n    p=load_game(save_path)\n    if p is None:\n        print('No V2 save found')\n        return\n    game_loop(p, save_path)\nelse:\n    return"
                    }
                ]
            }
        ]
    }

    run_aish_tool("python_module_generator", json.dumps(module_spec))


if __name__ == "__main__":
    main()
