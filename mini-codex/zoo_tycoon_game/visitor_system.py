import random

def daily_visitors(rng, weekend=False):
    base = 220 if weekend else 160
    return max(20, round(rng.gauss(base, 45)))