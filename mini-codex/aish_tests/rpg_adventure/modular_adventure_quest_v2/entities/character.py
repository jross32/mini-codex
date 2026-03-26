"""V2 character functions"""
def new_character(name):
    return {'name': name, 'level': 1, 'exp': 0, 'hp': 120, 'max_hp': 120, 'strength': 12, 'defense': 4, 'gold': 100, 'inventory': []}


def character_take_damage(player, dmg):
    final = max(1, dmg - player['defense'] // 2)
    player['hp'] = max(0, player['hp'] - final)
    return final


def character_heal(player, amt):
    player['hp'] = min(player['max_hp'], player['hp'] + amt)
    return player['hp']


def character_gain_exp(player, amt):
    player['exp'] += amt
    need = player['level'] * 100
    if player['exp'] >= need:
        player['exp'] -= need
        player['level'] += 1
        player['max_hp'] += 20
        player['hp'] = player['max_hp']
        player['strength'] += 2
        player['defense'] += 1
        return True
    return False


def character_is_alive(player):
    return player['hp'] > 0

