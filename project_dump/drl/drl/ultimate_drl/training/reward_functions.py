
from __future__ import annotations

from math import sqrt
from ..config import DRLConfig


def compute_reward(
    step_return: float,
    drawdown: float,
    volatility_regime: int,
    benchmark_return: float,
    trading_cost: float,
    overtrading_factor: float,
    config: DRLConfig,
) -> float:
    """Multi-objective reward for trading.

    Components:
    - PnL: raw per-step equity change
    - Drawdown penalty
    - Volatility-aware penalty (heavier penalty in high-vol regimes)
    - Trading cost penalty
    - Overtrading penalty (too many trades per bar)
    - Benchmark-relative term (encourage beating benchmark)
    """

    # Primary return component
    r_pnl = config.reward_pnl_weight * step_return

    # Drawdown (drawdown is negative or zero)
    r_dd = config.reward_drawdown_penalty * drawdown

    # Volatility regime penalty - heavier penalty when in high volatility regimes
    vol_factor = 1.0 + 0.5 * volatility_regime  # 0 -> 1.0, 1 -> 1.5, 2 -> 2.0
    r_vol = -config.reward_volatility_penalty * abs(step_return) * vol_factor

    # Trading cost and overtrading
    r_cost = -config.reward_trading_cost_penalty * trading_cost
    r_over = -config.reward_overtrading_penalty * overtrading_factor

    # Benchmark: encourage outperformance
    excess_return = step_return - benchmark_return
    r_bench = config.reward_benchmark_weight * excess_return

    reward = r_pnl + r_dd + r_vol + r_cost + r_over + r_bench
    return float(reward)
