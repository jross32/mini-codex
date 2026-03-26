"""V2 combat functions"""
import random
from entities.character import character_take_damage
from entities.monster import monster_is_alive

def player_attack(player, monster):
    raw = player['strength'] + random.randint(1,6)
    dmg = max(1, raw - monster['def'])
    monster['hp'] = max(0, monster['hp'] - dmg)
    return dmg


def enemy_attack(player, monster):
    raw = monster['atk'] + random.randint(0,4)
    return character_take_damage(player, raw)


def combat_round(player, monster):
    p = player_attack(player, monster)
    m = 0
    if monster_is_alive(monster):
        m = enemy_attack(player, monster)
    return {'player_damage': p, 'enemy_damage': m}

