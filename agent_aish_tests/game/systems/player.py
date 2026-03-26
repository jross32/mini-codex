"""Player state helpers for generated adventure variants."""
def create_player():
    """Create a default player state."""
    return {
        'level': 1,
        'xp': 0,
        'gold': 0,
        'hp': 20,
        'inventory': ['field map'],
    }


def rest_player(player):
    """Recover some HP while preserving upper cap."""
    player['hp'] = min(20 + (player['level'] - 1) * 4, player['hp'] + 5)
    return player

