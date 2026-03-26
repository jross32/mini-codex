import random

POSITIVE = [('viral_post', 1.3, 0), ('celebrity_visit', 1.5, 0), ('baby_born', 1.6, 0)]
NEGATIVE = [('escape', 0.8, 8000), ('storm', 0.9, 5000), ('strike', 0.7, 2000)]

def season(day):
    return ['spring', 'summer', 'autumn', 'winter'][((day - 1) // 91) % 4]

def roll_event(rng):
    r = rng.random()
    if r < 0.08:
        name, boost, cost = rng.choice(POSITIVE)
        return {'name': name, 'boost': boost, 'cost': cost}
    if r < 0.15:
        name, pen, cost = rng.choice(NEGATIVE)
        return {'name': name, 'boost': pen, 'cost': cost}
    return None