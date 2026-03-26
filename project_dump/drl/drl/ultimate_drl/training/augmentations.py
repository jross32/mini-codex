
from __future__ import annotations

from ..config import DRLConfig


def maybe_augment_step(
    reward: float,
    step_return: float,
    drawdown: float,
    volatility_regime: int,
    idx: int,
    total_steps: int,
    config: DRLConfig,
) -> float:
    """Simple curriculum / augmentation hook.

    - Early in training (first 30% of steps), we soften penalties to let the agent explore.
    - Later in training, we amplify risk penalties to force robustness.
    - In high-volatility regimes, we slightly increase the cost of large negative returns.
    """

    progress = idx / max(total_steps, 1)
    new_reward = reward

    # Early phase: encourage exploration => slightly boost positive returns
    if progress < 0.3:
        if step_return > 0:
            new_reward += 0.1 * step_return

    # Late phase: more disciplined
    if progress > 0.7:
        # Extra penalty for drawdowns and large negative returns
        if drawdown < 0:
            new_reward += 0.5 * drawdown
        if step_return < 0:
            new_reward += 0.2 * step_return

    # Volatility-aware tweak
    if volatility_regime == 2 and step_return < 0:
        # Additional small penalty in very volatile regimes for big losses
        new_reward += 0.1 * step_return

    return float(new_reward)
