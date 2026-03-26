import random

CATALOGUE = [
    ('lion', 'savanna', 18000, 850),
    ('elephant', 'savanna', 22000, 1200),
    ('penguin', 'arctic', 3000, 350),
    ('gorilla', 'rainforest', 20000, 1100),
    ('giraffe', 'savanna', 4000, 400),
    ('tiger', 'rainforest', 21000, 1000),
]

def select_species(rng):
    return rng.choice(CATALOGUE)

def health_tick(health, keeper='trained'):
    decay = {'novice': 3.5, 'trained': 1.5, 'expert': 0.5}.get(keeper, 1.5)
    return round(max(0.0, health - decay), 1)

def behavior(health):
    if health >= 80: return 'playing'
    if health >= 60: return 'active'
    if health >= 40: return 'resting'
    return 'lethargic'