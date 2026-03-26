
import gym
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any

from ..config import DRLConfig
from ..training.reward_functions import compute_reward
from ..training.augmentations import maybe_augment_step
from ..utils.metrics import compute_volatility_regime


class TradingEnv(gym.Env):
    """Research-style trading environment.

    Key features:
    - Multi-asset capable (for now, we focus on single-asset but keep API generic).
    - Continuous action space: position fraction in [-max_position, max_position].
    - Regime features: simple volatility regime label injected into the observation.
    - Reward uses a multi-objective function (see reward_functions.compute_reward).
    - Integrated slippage + fees.
    - Hard risk constraints (daily loss, leverage cap).

    Requirements:
    - price_df must have at least a 'close' column.
    - You can optionally pass 'high', 'low', 'open', 'volume' for richer future features.
    """

    metadata = {"render.modes": ["human"]}

    def __init__(
        self,
        price_df: pd.DataFrame,
        config: DRLConfig,
        benchmark_close: Optional[pd.Series] = None,
    ) -> None:
        super().__init__()
        self.config = config
        self.price_df = price_df.reset_index(drop=True)
        self.benchmark_close = (
            benchmark_close.reset_index(drop=True)
            if benchmark_close is not None
            else None
        )

        if "close" not in self.price_df.columns:
            raise ValueError("price_df must contain a 'close' column.")

        self.window = int(self.config.window_size)
        if len(self.price_df) <= self.window + 2:
            raise ValueError("price_df is too short for the configured window.")

        # Precompute regime labels (0 = low vol, 1 = medium, 2 = high)
        self.regimes = compute_volatility_regime(self.price_df["close"], window=30)

        # Observation space: window of normalized closes + regime + [position, equity, equity_peak]
        self.num_price_features = 1  # just close normalized for now
        obs_size = self.window * self.num_price_features + 3 + 1  # +3 state +1 regime

        self.observation_space = gym.spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(obs_size,),
            dtype=np.float32,
        )

        # Action is in [-1, 1] => scaled to [-max_position_pct, max_position_pct]
        self.action_space = gym.spaces.Box(
            low=-1.0, high=1.0, shape=(1,), dtype=np.float32
        )

        self._reset_state()

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------
    def _reset_state(self) -> None:
        self.idx = self.window
        self.equity = 1.0
        self.initial_equity = 1.0
        self.position = 0.0
        self.entry_price: Optional[float] = None
        self.equity_peak = self.equity
        self.cumulative_trading_costs = 0.0
        self.trades_count = 0

    def reset(self) -> np.ndarray:
        self._reset_state()
        return self._get_observation()

    def step(self, action: np.ndarray):
        a = float(np.clip(action[0], -1.0, 1.0))
        target_position = a * float(self.config.max_position_pct)

        price = self._get_price(self.idx)
        prev_equity = self.equity

        # Realized PnL for existing position
        pnl = 0.0
        if self.entry_price is not None and self.position != 0.0:
            price_change = (price / self.entry_price) - 1.0
            pnl = self.position * prev_equity * price_change

        # Position change cost with slippage + fees
        position_change = abs(target_position - self.position)
        notional = prev_equity * position_change
        # Basis points to fraction
        slippage = (self.config.slippage_bps / 10_000.0) * notional
        fees = (self.config.fee_bps / 10_000.0) * notional
        trading_cost = slippage + fees
        self.cumulative_trading_costs += trading_cost

        # Update equity
        self.equity = prev_equity + pnl - trading_cost
        self.equity_peak = max(self.equity_peak, self.equity)

        # Update position and entry price
        traded = position_change > 1e-6
        if traded:
            self.trades_count += 1
        self.position = target_position
        self.entry_price = price if self.position != 0.0 else None

        # Benchmark
        benchmark_return = 0.0
        if self.benchmark_close is not None and self.idx > 0:
            prev_benchmark = float(self.benchmark_close.iloc[self.idx - 1])
            cur_benchmark = float(self.benchmark_close.iloc[self.idx])
            if prev_benchmark > 0:
                benchmark_return = (cur_benchmark / prev_benchmark) - 1.0

        # Raw step return + features for reward
        step_return = (self.equity / max(prev_equity, 1e-8)) - 1.0
        drawdown = (self.equity / max(self.equity_peak, 1e-8)) - 1.0
        overtrading_factor = float(self.trades_count) / float(
            max(self.idx - self.window, 1)
        )

        reward = compute_reward(
            step_return=step_return,
            drawdown=drawdown,
            volatility_regime=int(self.regimes[self.idx]),
            benchmark_return=benchmark_return,
            trading_cost=trading_cost,
            overtrading_factor=overtrading_factor,
            config=self.config,
        )

        # Curriculum / augmentations hook
        if self.config.use_augmentations:
            reward = maybe_augment_step(
                reward=reward,
                step_return=step_return,
                drawdown=drawdown,
                volatility_regime=int(self.regimes[self.idx]),
                idx=self.idx,
                total_steps=len(self.price_df),
                config=self.config,
            )

        # Risk & episode termination
        done = False
        info: Dict[str, Any] = {}

        # Daily loss style constraint relative to starting equity
        if (self.equity - self.initial_equity) <= -float(
            self.config.max_daily_loss_pct
        ):
            done = True
            info["reason"] = "max_daily_loss_reached"

        # End of data
        self.idx += 1
        if self.idx >= len(self.price_df):
            done = True
            info.setdefault("reason", "end_of_data")

        obs = self._get_observation()
        return obs, float(reward), done, info

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_price(self, idx: int) -> float:
        return float(self.price_df.iloc[idx]["close"])

    def _get_observation(self) -> np.ndarray:
        start = self.idx - self.window
        end = self.idx
        window_df = self.price_df.iloc[start:end]
        closes = window_df["close"].values.astype(np.float32)

        base = closes[0] if closes[0] != 0 else 1.0
        norm_closes = (closes / base) - 1.0
        price_features = norm_closes.reshape(-1)

        # Regime feature
        regime = float(self.regimes[self.idx])

        state = np.array(
            [self.position, self.equity, self.equity_peak, regime], dtype=np.float32
        )

        obs = np.concatenate([price_features, state])
        return obs

    def render(self, mode: str = "human") -> None:
        price = self._get_price(self.idx)
        print(
            f"idx={self.idx}, price={price:.4f}, equity={self.equity:.4f}, "
            f"position={self.position:.3f}, regime={self.regimes[self.idx]}"
        )
