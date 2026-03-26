"""Encounter sampling for generated game variant."""
import random

def roll_encounter(threat_bias='medium'):
    """Sample one encounter payload with a coarse threat bias."""
    threat_pool = ['low', 'medium', 'high']
    if threat_bias == 'high':
        threat_pool = ['medium', 'high', 'high']
    elif threat_bias == 'low':
        threat_pool = ['low', 'low', 'medium']
    enemy = {
        'name': 'Sable Warden',
        'threat': random.choice(threat_pool),
        'xp_reward': random.randint(8, 16),
        'gold_reward': random.randint(3, 9),
    }
    return enemy


def resolve_encounter(player, encounter):
    """Resolve a combat exchange and return outcome data."""
    difficulty = {'low': 5, 'medium': 8, 'high': 11}[encounter['threat']]
    power = player['level'] + player['hp'] // 8
    won = power >= difficulty
    if not won:
        player['hp'] = max(1, player['hp'] - difficulty)
    return {
        'won': won,
        'damage_taken': 0 if won else difficulty,
        'xp_reward': encounter['xp_reward'] if won else encounter['xp_reward'] // 2,
        'gold_reward': encounter['gold_reward'] if won else 0,
    }

