
# Ultimate DRL Trading Agent (Research-Grade Core)

This folder contains a **research-style DRL core** for your AI trading bot.
It focuses purely on **backtesting, walk-forward training, and ensemble DRL**
for stocks/crypto. No Flask, no broker APIs — those will hook into this later.

## Key features

- **Ensemble DRL Agent**
  - Trains **PPO + SAC + DDPG** and aggregates their actions.
  - Uses Stable-Baselines3 under the hood.
- **Walk-Forward Training**
  - `training.walkforward.train_walkforward_ensemble` splits data into
    rolling train/test windows and evaluates each.
- **Multi-Objective Reward**
  - Combines per-step PnL, drawdown, volatility-aware penalties,
    trading costs, overtrading penalties, and benchmark outperformance.
- **Volatility Regimes**
  - Simple volatility classifier (low/med/high) used as a feature
    and in the reward shaping.
- **Curriculum / Augmentations**
  - Early vs late training reward tweaks to encourage exploration
    first and discipline later.

## Layout

- `ultimate_drl/config.py`
  - `DRLConfig`: dataclass for strategy, risk, reward knobs.
  - `StrategyPreset` and `get_presets()`: ready-made strategy templates.

- `ultimate_drl/envs/trading_env.py`
  - `TradingEnv`: Gym environment for single-asset trading.
  - Includes:
    - slippage + fee modeling (basis points)
    - volatility regime feature
    - multi-objective reward via `training.reward_functions`

- `ultimate_drl/agents/ensemble_agent.py`
  - `EnsembleDRLAgent`: trains PPO, SAC, DDPG, aggregates actions.

- `ultimate_drl/training/reward_functions.py`
  - `compute_reward`: central reward logic.

- `ultimate_drl/training/augmentations.py`
  - `maybe_augment_step`: curriculum & reward augmentation hook.

- `ultimate_drl/training/walkforward.py`
  - `generate_walkforward_splits`: simple rolling train/test split.
  - `train_walkforward_ensemble`: end-to-end walk-forward training loop.

- `ultimate_drl/utils/metrics.py`
  - `evaluate_episode_metrics`: returns total return, volatility,
    Sharpe-like ratio, max drawdown, etc.
  - `compute_volatility_regime`: labels each bar as low/med/high vol.

- `ultimate_drl/utils/data_utils.py`
  - `load_price_csv`: convenience loader for CSV price data.

- `scripts/example_train.py`
  - Minimal example to train an ensemble on a CSV.

## Install

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
```

## Quick start: run example training

```bash
python scripts/example_train.py --csv path/to/your_data.csv --preset "Swing (Conservative)" --timesteps 100000
```

The CSV **must** have at least a `close` column. Other columns are ignored
for now but can be wired in later as features.

## How to integrate into your Flask app later

- Treat `ultimate_drl` as a standalone package.
- Your Flask app will:
  - Construct a `DRLConfig` (or use `get_presets()` and tweak) based on
    user settings.
  - Pass historical OHLCV data as a `pandas.DataFrame` to the training
    functions or directly to `TradingEnv`.
  - Use `EnsembleDRLAgent` to train models and save model IDs per user.
  - In live/paper trading mode, load the trained models and call
    `predict_ensemble_action()` on each new observation.
- All real trading (Alpaca, Binance, etc.) is **outside** this core; you
  simply convert position fractions to order sizes and send them via APIs.
