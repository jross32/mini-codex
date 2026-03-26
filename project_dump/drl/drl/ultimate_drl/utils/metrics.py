
from __future__ import annotations

from typing import List
import numpy as np
import pandas as pd


def evaluate_episode_metrics(equities: List[float], rewards: List[float]) -> dict:
    """Compute basic performance stats from a single episode."""
    equities = np.array(equities, dtype=float)
    rewards = np.array(rewards, dtype=float)

    total_return = float(equities[-1] / equities[0] - 1.0)
    returns = np.diff(equities) / equities[:-1]
    avg_return = float(np.mean(returns)) if len(returns) > 0 else 0.0
    vol = float(np.std(returns)) if len(returns) > 0 else 0.0

    sharpe = float(avg_return / (vol + 1e-8)) if vol > 0 else 0.0

    # Max drawdown
    peak = np.maximum.accumulate(equities)
    dd = (equities / (peak + 1e-8)) - 1.0
    max_dd = float(np.min(dd))

    return {
        "total_return": total_return,
        "avg_step_return": avg_return,
        "volatility": vol,
        "sharpe_like": sharpe,
        "max_drawdown": max_dd,
        "sum_rewards": float(np.sum(rewards)),
    }


def compute_volatility_regime(close: pd.Series, window: int = 30) -> pd.Series:
    """Very simple volatility regime classifier.

    - Compute rolling std of log returns.
    - Split into tertiles: low, medium, high volatility regimes (0, 1, 2).
    """

    log_returns = np.log(close / close.shift(1)).fillna(0.0)
    rolling_vol = log_returns.rolling(window=window, min_periods=1).std().fillna(0.0)

    # Tertile thresholds
    q1 = rolling_vol.quantile(1 / 3)
    q2 = rolling_vol.quantile(2 / 3)

    def assign_regime(v: float) -> int:
        if v <= q1:
            return 0
        elif v <= q2:
            return 1
        else:
            return 2

    regimes = rolling_vol.apply(assign_regime)
    return regimes
