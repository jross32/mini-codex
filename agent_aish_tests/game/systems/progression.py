"""Progression and reward logic for generated game variants."""
def apply_rewards(player, outcome):
    """Apply rewards and handle level-ups."""
    player['xp'] += outcome['xp_reward']
    player['gold'] += outcome['gold_reward']
    threshold = 20 + (player['level'] - 1) * 10
    while player['xp'] >= threshold:
        player['xp'] -= threshold
        player['level'] += 1
        player['hp'] += 4
        threshold = 20 + (player['level'] - 1) * 10
    return player

