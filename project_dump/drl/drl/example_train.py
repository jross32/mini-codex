
"""Minimal training example for the DRL agent core.

This script assumes you have a CSV file with at least a 'close' column.
It will:
- Load the CSV
- Configure a simple Swing preset
- Train a PPO model for a small number of timesteps
"""

import argparse
import pandas as pd

from drl_agent_core.drl_agent import DRLAgent, PRESETS, DRLConfig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, required=True, help="Path to OHLCV CSV with at least a 'close' column.")
    parser.add_argument("--timesteps", type=int, default=50_000, help="Number of training timesteps.")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    if "close" not in df.columns:
        raise ValueError("CSV must have a 'close' column.")

    base_cfg = PRESETS["Swing (Balanced)"]
    config = DRLConfig(
        symbols=["DEMO"],
        timeframe=base_cfg.timeframe,
        exchange=base_cfg.exchange,
        strategy_type=base_cfg.strategy_type,
        risk_mode=base_cfg.risk_mode,
        objective=base_cfg.objective,
        train_window_days=base_cfg.train_window_days,
        test_window_days=base_cfg.test_window_days,
        walkforward_steps=base_cfg.walkforward_steps,
        algorithm=base_cfg.algorithm,
        total_timesteps=args.timesteps,
        max_position_pct=base_cfg.max_position_pct,
        max_daily_loss_pct=base_cfg.max_daily_loss_pct,
        max_open_trades=base_cfg.max_open_trades,
        reward_pnl_weight=base_cfg.reward_pnl_weight,
        reward_drawdown_penalty=base_cfg.reward_drawdown_penalty,
        reward_trading_cost_penalty=base_cfg.reward_trading_cost_penalty,
        reward_position_penalty=base_cfg.reward_position_penalty,
        seed=42,
    )

    agent = DRLAgent(model_dir="models")
    run_id = agent.start_training(df, config)
    print("Training complete. run_id=", run_id)


if __name__ == "__main__":
    main()
