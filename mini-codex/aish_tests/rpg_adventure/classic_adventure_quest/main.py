#!/usr/bin/env python3
"""Complete interactive CLI RPG adventure game."""
import json
import os
import time
import sys
import random
from pathlib import Path

# ============ CHARACTER SYSTEM ============
class Character:
    def __init__(self, name, level=1, exp=0):
        self.name = name
        self.level = level
        self.exp = exp
        self.hp = 100
        self.max_hp = 100
        self.strength = 10
        self.defense = 3
        self.wisdom = 8
        self.gold = 0

    def take_damage(self, dmg):
        reduced = max(1, dmg - self.defense // 2)
        self.hp = max(0, self.hp - reduced)

    def heal(self, amt):
        self.hp = min(self.max_hp, self.hp + amt)

    def gain_exp(self, amt):
        self.exp += amt
        if self.exp >= self.level * 100:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.max_hp += 20
        self.hp = self.max_hp
        self.strength += 2
        self.defense += 1
        self.wisdom += 1
        self.exp = 0

    def is_alive(self):
        return self.hp > 0

# ============ MONSTER SYSTEM ============
class Monster:
    def __init__(self, name, hp, attk, dfn, level, loot):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attack = attk
        self.defense = dfn
        self.level = level
        self.loot = loot

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)

    def is_alive(self):
        return self.hp > 0

    def compute_attack(self):
        var = random.randint(-3, 3)
        return max(1, self.attack + var)

def spawn_monster(level):
    types = [
        ("Goblin", 10, 3, 1, 1, {"gold": 50}),
        ("Orc", 25, 7, 2, 3, {"gold": 150}),
        ("Troll", 40, 10, 3, 5, {"gold": 300}),
        ("Dragon", 100, 15, 5, 10, {"gold": 1000, "rare": True}),
    ]
    idx = min(level - 1, len(types) - 1)
    t = types[idx]
    return Monster(t[0], t[1] * level, t[2] + level, t[3] + level // 2, level, t[5])

# ============ COMBAT SYSTEM ============
class Combat:
    def __init__(self, player, monster):
        self.player = player
        self.monster = monster
        self.turns = 0

    def player_attack(self):
        dmg = self.player.strength + random.randint(1, 5)
        self.monster.take_damage(dmg)
        return dmg

    def monster_attack(self):
        dmg = self.monster.compute_attack()
        self.player.take_damage(dmg)
        return dmg

    def is_over(self):
        return not self.monster.is_alive() or self.player.hp <= 0

    def resolve(self):
        p_dmg = self.player_attack()
        m_dmg = 0 if not self.monster.is_alive() else self.monster_attack()
        self.turns += 1
        return p_dmg, m_dmg

# ============ UI SYSTEM ============
class UI:
    @staticmethod
    def clear():
        print(chr(27) + "[2J" + chr(27) + "[H")

    @staticmethod
    def loading_bar(msg="Loading", dur=0.5):
        iters = int(dur * 100)
        for i in range(101):
            filled = int(30 * i / 100)
            bar = "#" * filled + "-" * (30 - filled)
            sys.stdout.write(f"\r{msg}: [{bar}] {i}%")
            sys.stdout.flush()
            if i < 100:
                time.sleep(0.005)
        print()

    @staticmethod
    def title(txt="=== ADVENTURE QUEST ==="):
        print(); print(txt.center(80)); print()

    @staticmethod
    def menu(opts):
        for i, o in enumerate(opts, 1):
            print(f"{i}. {o}")

    @staticmethod
    def status(p):
        print(f"LVL {p.level} | HP {p.hp}/{p.max_hp} | EXP {p.exp}/{p.level*100} | GOLD {p.gold}")

    @staticmethod
    def animate(txt, spd=0.02):
        for c in txt:
            sys.stdout.write(c); sys.stdout.flush(); time.sleep(spd)
        print()

# ============ SHOP SYSTEM ============
class Shop:
    @staticmethod
    def items():
        base = [("Health Potion", 50), ("Antidote", 100)]
        if random.random() < 0.2:
            base.extend([("Legendary Sword", 2000), ("Dragon Armor", 3000)])
        return base

    @staticmethod
    def rare_trader():
        if random.random() < 0.1:
            return {"name": "Mysterious Wanderer", "goods": "Rare Artifacts"}
        return None

# ============ REST SYSTEM ============
REST_PLACES = [
    ("Inn", 75, 50),
    ("Shrine", 100, 100),
    ("Temple", 150, 200),
]

# ============ SAVE/LOAD ============
def save_game(p):
    data = {"name": p.name, "level": p.level, "exp": p.exp, "hp": p.hp, "max_hp": p.max_hp, "str": p.strength, "def": p.defense, "gold": p.gold}
    Path("aish_tests").mkdir(exist_ok=True)
    with open("aish_tests/save.json", "w") as f:
        json.dump(data, f)

def load_game():
    try:
        if os.path.exists("aish_tests/save.json"):
            with open("aish_tests/save.json") as f:
                d = json.load(f)
            p = Character(d["name"], d["level"], d["exp"])
            p.hp, p.max_hp, p.strength, p.defense, p.gold = d["hp"], d["max_hp"], d["str"], d["def"], d["gold"]
            return p
    except:
        pass
    return None

# ============ GAME LOOP ============
def game_loop(player, ui):
    while player.is_alive():
        ui.clear()
        ui.status(player)
        print("\n1. Explore (Fight)\n2. Rest\n3. Shop\n4. Save\n5. Quit")
        choice = input(">> ").strip()
        
        if choice == "1":
            explore(player, ui)
        elif choice == "2":
            rest_menu(player, ui)
        elif choice == "3":
            shop_menu(player, ui)
        elif choice == "4":
            save_game(player)
            print("[OK] Game saved!")
            time.sleep(1)
        elif choice == "5":
            print("Thanks for playing!"); break

def explore(player, ui):
    mon = spawn_monster(player.level)
    ui.animate(f"A wild {mon.name} appears!\n")
    combat = Combat(player, mon)
    
    while not combat.is_over():
        print(f"\n{mon.name} HP: {mon.hp}")
        print("1. Attack\n2. Run (50%)")
        c = input(">> ").strip()
        
        if c == "1":
            p_dmg, m_dmg = combat.resolve()
            print(f"You hit for {p_dmg} dmg!")
            if mon.is_alive():
                print(f"{mon.name} hits for {m_dmg} dmg!")
        elif c == "2" and random.random() > 0.5:
            print("You escaped!"); return
    
    if player.hp > 0:
        ui.title(); print(f"Victory! Defeated {mon.name}")
        player.gain_exp(mon.level * 50)
        player.gold += mon.loot.get("gold", 0)
        print(f"Gained {mon.level * 50} EXP, {mon.loot.get('gold', 0)} gold!")
    else:
        print("YOU DIED!"); player.hp = player.max_hp
    
    input(">> "); ui.clear()

def rest_menu(player, ui):
    for i, (n, h, c) in enumerate(REST_PLACES, 1):
        print(f"{i}. {n} (heal {h}, costs {c} gold)")
    c = int(input(">> ") or "0") - 1
    if 0 <= c < len(REST_PLACES):
        n, h, cost = REST_PLACES[c]
        if player.gold >= cost:
            player.heal(h); player.gold -= cost
            print(f"Rested at {n}. HP restored!")
            time.sleep(1)
        else:
            print("Not enough gold!")

def shop_menu(player, ui):
    items = Shop.items()
    print("Items for sale:")
    for i, (n, p) in enumerate(items, 1):
        print(f"{i}. {n} - {p} gold")
    c = int(input("Buy (0 skip): ") or "0") - 1
    if 0 <= c < len(items):
        n, price = items[c]
        if player.gold >= price:
            player.gold -= price
            print(f"Bought {n}!")
        else:
            print("Not enough gold!")

def main():
    ui = UI()
    ui.clear(); ui.loading_bar(); ui.title()
    
    print("Welcome adventurer!")
    print("1. New Game\n2. Load Game\n3. Exit")
    choice = input(">> ").strip()
    
    if choice == "1":
        name = input("Character name: ").strip() or "Hero"
        player = Character(name)
        game_loop(player, ui)
    elif choice == "2":
        player = load_game()
        if player:
            print(f"Welcome back, {player.name}!")
            time.sleep(1)
            game_loop(player, ui)
        else:
            print("No save found!")
    else:
        print("Goodbye!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGame interrupted.")
