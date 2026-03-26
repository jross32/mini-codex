"""V2 rest functions"""
def rest_locations():
    return [('Inn',80,60),('Shrine',120,110),('Temple',180,210)]


def apply_rest(player, choice_index):
    spots=rest_locations()
    if choice_index < 0 or choice_index >= len(spots):
        return {'ok': False, 'reason': 'invalid'}
    name, heal, cost = spots[choice_index]
    if player['gold'] < cost:
        return {'ok': False, 'reason': 'gold'}
    player['gold'] -= cost
    player['hp'] = min(player['max_hp'], player['hp'] + heal)
    return {'ok': True, 'name': name, 'heal': heal, 'cost': cost}

