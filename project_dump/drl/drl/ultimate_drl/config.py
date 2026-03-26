
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Dict, List, Optional

STRATEGY_TYPES = Literal["scalping", "intraday_trend", "swing_trend", "position"]
RISK_MODES = Literal["conservative", "balanced", "aggressive"]
OBJECTIVE_TYPES = Literal["risk_adjusted_return", "pure_return", "drawdown_minimization"]


@dataclass
class DRLConfig:
    """Configuration object for the DRL agent.

    This is what your UI / JSON will eventually map to.
    """

    # What to train on
    symbols: List[str]
    timeframe: str
    exchange: str

    # Strategy profile
    strategy_type: STRATEGY_TYPES
    risk_mode: RISK_MODES
    objective: OBJECTIVE_TYPES

    # Training regime
    train_window_days: int
    test_window_days: int
    walkforward_steps: int
    total_timesteps: int
    algo_list: List[str]  # e.g. ["PPO", "SAC", "DDPG"]

    # Risk controls
    max_position_pct: float
    max_daily_loss_pct: float
    max_total_leverage: float
    max_open_trades: int

    # Reward shaping
    reward_pnl_weight: float
    reward_drawdown_penalty: float
    reward_volatility_penalty: float
    reward_trading_cost_penalty: float
    reward_overtrading_penalty: float
    reward_benchmark_weight: float

    gamma: float = 0.99
    seed: Optional[int] = None

    # Data / environment knobs
    window_size: int = 64
    slippage_bps: float = 1.0  # basis points
    fee_bps: float = 10.0      # basis points

    # Curriculum / augmentation flags
    use_volatility_curriculum: bool = True
    use_augmentations: bool = True


@dataclass
class StrategyPreset:
    name: str
    config: DRLConfig


def _base_template() -> DRLConfig:
    # This acts as a generic, balanced template that we can clone and tweak.
    return DRLConfig(
        symbols=[],
        timeframe="1h",
        exchange="generic",
        strategy_type="swing_trend",
        risk_mode="balanced",
        objective="risk_adjusted_return",
        train_window_days=365,
        test_window_days=60,
        walkforward_steps=3,
        total_timesteps=300_000,
        algo_list=["PPO", "SAC", "DDPG"],
        max_position_pct=0.3,
        max_daily_loss_pct=0.03,
        max_total_leverage=1.0,
        max_open_trades=3,
        reward_pnl_weight=1.0,
        reward_drawdown_penalty=1.0,
        reward_volatility_penalty=0.3,
        reward_trading_cost_penalty=0.4,
        reward_overtrading_penalty=0.2,
        reward_benchmark_weight=0.3,
        gamma=0.99,
        seed=42,
        window_size=64,
        slippage_bps=1.0,
        fee_bps=10.0,
        use_volatility_curriculum=True,
        use_augmentations=True,
    )


def get_presets() -> Dict[str, StrategyPreset]:
    """Return a dict of high-level strategy presets.

    You can extend or modify these however you want in your app.
    """

    presets: Dict[str, StrategyPreset] = {}

    # Scalping (Aggressive)
    scalping = _base_template()
    scalping.strategy_type = "scalping"
    scalping.risk_mode = "aggressive"
    scalping.timeframe = "1m"
    scalping.train_window_days = 30
    scalping.test_window_days = 7
    scalping.total_timesteps = 500_000
    scalping.max_position_pct = 0.7
    scalping.max_daily_loss_pct = 0.06
    scalping.reward_volatility_penalty = 0.1
    scalping.reward_trading_cost_penalty = 0.6
    scalping.reward_overtrading_penalty = 0.3
    presets["Scalping (Aggressive)"] = StrategyPreset(
        name="Scalping (Aggressive)",
        config=scalping,
    )

    # Intraday trend (Balanced)
    intraday = _base_template()
    intraday.strategy_type = "intraday_trend"
    intraday.risk_mode = "balanced"
    intraday.timeframe = "5m"
    intraday.train_window_days = 90
    intraday.test_window_days = 14
    intraday.total_timesteps = 400_000
    intraday.max_position_pct = 0.5
    intraday.max_daily_loss_pct = 0.04
    presets["Intraday Trend (Balanced)"] = StrategyPreset(
        name="Intraday Trend (Balanced)",
        config=intraday,
    )

    # Swing (Conservative)
    swing = _base_template()
    swing.strategy_type = "swing_trend"
    swing.risk_mode = "conservative"
    swing.timeframe = "4h"
    swing.train_window_days = 730
    swing.test_window_days = 90
    swing.total_timesteps = 300_000
    swing.max_position_pct = 0.25
    swing.max_daily_loss_pct = 0.02
    swing.reward_volatility_penalty = 0.5
    swing.reward_drawdown_penalty = 1.2
    presets["Swing (Conservative)"] = StrategyPreset(
        name="Swing (Conservative)",
        config=swing,
    )

    # Position / long-term
    position = _base_template()
    position.strategy_type = "position"
    position.risk_mode = "conservative"
    position.timeframe = "1d"
    position.train_window_days = 5 * 365
    position.test_window_days = 365
    position.total_timesteps = 200_000
    position.max_position_pct = 0.5
    position.max_daily_loss_pct = 0.03
    position.reward_benchmark_weight = 0.6  # really wants to beat benchmark
    presets["Long-Term Position"] = StrategyPreset(
        name="Long-Term Position",
        config=position,
    )

    return presets
