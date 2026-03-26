from random import Random

from core.engine import Engine
from systems.bar.simulation import BarState, run_shift, score


def choose_action(day: int) -> str:
    cycle = ["import_stock", "street_promo", "tight_security", "hold"]
    return cycle[(day - 1) % len(cycle)]


def run_game(days: int = 7) -> dict:
    engine = Engine()
    rng = Random(2077)
    state = BarState()

    print("=== CYBERPUNK BAR MANAGEMENT SIM ===")
    for _ in range(days):
        action = choose_action(state.day)
        report = run_shift(state, action, rng)
        engine.next_tick()
        print(
            f"Day {report['day']}: action={report['action']} crowd={report['crowd']} "
            f"served={report['served']} cash={report['cash']} stock={report['stock']} "
            f"rep={report['reputation']} stress={report['stress']}"
        )

    final_score = score(state)
    print(f"Final score: {final_score}")
    return {"days": days, "cash": state.cash, "stock": state.stock, "reputation": state.reputation, "stress": state.stress, "score": final_score}


if __name__ == "__main__":
    run_game()
