
"""Ultimate DRL trading agent package.

This package is **framework-only** – no Flask, no broker APIs.
It provides:

- A rich trading environment with regime features, slippage and risk constraints.
- Config system for strategies, risk and objectives.
- A research-style training stack:
  - Walk-forward training
  - Curriculum hooks
  - Advanced reward functions
- An ensemble DRL agent that combines PPO, SAC and DDPG policies.
"""

from .config import DRLConfig, StrategyPreset, OBJECTIVE_TYPES, RISK_MODES, STRATEGY_TYPES
from .agents.ensemble_agent import EnsembleDRLAgent
from .envs.trading_env import TradingEnv

__all__ = [
    "DRLConfig",
    "StrategyPreset",
    "OBJECTIVE_TYPES",
    "RISK_MODES",
    "STRATEGY_TYPES",
    "EnsembleDRLAgent",
    "TradingEnv",
]
