import math

def level_for_xp(total_xp: int) -> int:
    level = 1
    while total_xp >= 100 * (level ** 1.5):
        level += 1
    return max(1, level - 1)

def streak_multiplier(streak: int, cap: float = 2.0) -> float:
    return min(cap, 1 + streak * 0.05)
