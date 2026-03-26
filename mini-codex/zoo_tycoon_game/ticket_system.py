import random

def set_base_price(rng):
    return round(rng.uniform(10.0, 22.0), 2)

def surge(price, occ):
    m = 1.5 if occ >= 100 else 1.25 if occ >= 85 else 1.1 if occ >= 70 else 1.0
    return round(price * m, 2)

def child_price(adult):
    return round(adult * 0.5, 2)