"""Core cyberpunk bar simulation logic."""

from dataclasses import dataclass
from random import Random


@dataclass
class BarState:
    day: int = 1
    cash: int = 1200
    stock: int = 45
    reputation: int = 30
    stress: int = 10


def run_shift(state: BarState, action: str, rng: Random) -> dict:
    crowd = rng.randint(18, 42)
    demand = crowd + (state.reputation // 5)
    served = min(demand, state.stock)
    income = served * rng.randint(14, 24)

    state.stock -= served
    state.cash += income

    if action == "import_stock":
        buy = 24
        cost = buy * 8
        if state.cash >= cost:
            state.cash -= cost
            state.stock += buy
            state.reputation += 1
    elif action == "street_promo":
        state.cash = max(0, state.cash - 120)
        state.reputation += 3
        state.stress += 2
    elif action == "tight_security":
        state.cash = max(0, state.cash - 80)
        state.stress = max(0, state.stress - 2)
    else:
        state.stress += 1

    if state.stock < 10:
        state.reputation -= 2
        state.stress += 3

    state.reputation = max(0, min(100, state.reputation))
    state.stress = max(0, min(100, state.stress))

    report = {
        "day": state.day,
        "crowd": crowd,
        "served": served,
        "cash": state.cash,
        "stock": state.stock,
        "reputation": state.reputation,
        "stress": state.stress,
        "action": action,
    }
    state.day += 1
    return report


def score(state: BarState) -> int:
    return state.cash + (state.reputation * 25) - (state.stress * 15)
