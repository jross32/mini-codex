
from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from stable_baselines3.common.vec_env import DummyVecEnv

from ..config import DRLConfig
from ..envs.trading_env import TradingEnv
from ..agents.ensemble_agent import EnsembleDRLAgent
from ..utils.metrics import evaluate_episode_metrics


def generate_walkforward_splits(
    price_df: pd.DataFrame,
    config: DRLConfig,
) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """Generate walk-forward (train_df, test_df) splits.

    Very simple implementation: roll forward in chunks defined by
    train_window_days and test_window_days, assuming that each row of
    price_df is a bar of the chosen timeframe.
    """

    # Note: you can later map days -> bars based on timeframe.
    train_size = config.train_window_days
    test_size = config.test_window_days

    splits: List[Tuple[pd.DataFrame, pd.DataFrame]] = []
    start = 0
    while True:
        train_end = start + train_size
        test_end = train_end + test_size
        if test_end > len(price_df):
            break

        train_df = price_df.iloc[start:train_end].reset_index(drop=True)
        test_df = price_df.iloc[train_end:test_end].reset_index(drop=True)
        splits.append((train_df, test_df))

        start += test_size  # roll forward by test window

    return splits


def train_walkforward_ensemble(
    price_df: pd.DataFrame,
    config: DRLConfig,
    benchmark_close: pd.Series | None = None,
    model_dir: str = "models_walkforward",
) -> Dict:
    """Train an ensemble agent using walk-forward evaluation.

    Returns a dict containing:
    - 'runs': list of per-window metrics and model IDs
    - 'summary': aggregate performance metrics
    """

    splits = generate_walkforward_splits(price_df, config)
    agent = EnsembleDRLAgent(model_dir=model_dir)

    results: List[Dict] = []

    for i, (train_df, test_df) in enumerate(splits):
        print(f"[WF] Window {i+1}/{len(splits)} - train={len(train_df)} bars, test={len(test_df)} bars")

        # Train on train_df
        train_env_fn = lambda: TradingEnv(train_df, config=config, benchmark_close=benchmark_close)
        train_env = DummyVecEnv([train_env_fn])

        wf_run_id = f"wf_{i}"
        run_info = agent.train_ensemble(
            env=train_env,
            config=config,
            timesteps=config.total_timesteps,
            run_id=wf_run_id,
        )

        # Evaluate on test_df
        test_env = TradingEnv(test_df, config=config, benchmark_close=benchmark_close)
        obs = test_env.reset()
        done = False
        episode_rewards: List[float] = []
        equities: List[float] = [test_env.equity]

        while not done:
            action = agent.predict_ensemble_action(run_info["model_ids"], obs)
            obs, reward, done, info = test_env.step(action)
            episode_rewards.append(reward)
            equities.append(test_env.equity)

        metrics = evaluate_episode_metrics(equities=equities, rewards=episode_rewards)
        result_row = {
            "window_index": i,
            "train_size": len(train_df),
            "test_size": len(test_df),
            "config": asdict(config),
            "metrics": metrics,
            "model_ids": run_info["model_ids"],
        }
        results.append(result_row)

    # Aggregate simple stats
    all_returns = [r["metrics"]["total_return"] for r in results]
    summary = {
        "mean_total_return": float(np.mean(all_returns)),
        "std_total_return": float(np.std(all_returns)),
        "num_windows": len(results),
    }

    return {"runs": results, "summary": summary}
