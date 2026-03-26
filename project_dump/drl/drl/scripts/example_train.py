
"""Example script to train the Ultimate DRL ensemble on a single CSV.

Usage:
    python scripts/example_train.py --csv path/to/data.csv --preset "Swing (Conservative)" --timesteps 100000
"""

import argparse

from ultimate_drl.config import get_presets, DRLConfig
from ultimate_drl.utils.data_utils import load_price_csv
from ultimate_drl.training.walkforward import train_walkforward_ensemble


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, required=True, help="Path to CSV with at least a 'close' column.")
    parser.add_argument("--preset", type=str, default="Swing (Conservative)", help="Name of the strategy preset.")
    parser.add_argument("--timesteps", type=int, default=100_000, help="Training timesteps per walk-forward window.")
    args = parser.parse_args()

    presets = get_presets()
    if args.preset not in presets:
        raise ValueError(f"Unknown preset '{args.preset}'. Available: {list(presets.keys())}")

    base_preset = presets[args.preset]
    config: DRLConfig = base_preset.config
    # Timesteps override from CLI
    config.total_timesteps = args.timesteps

    df = load_price_csv(args.csv)

    print(f"Using preset: {args.preset}")
    result = train_walkforward_ensemble(price_df=df, config=config, benchmark_close=df['close'])

    print("=== Walk-forward summary ===")
    print(result["summary"])
    print(f"Windows: {len(result['runs'])}")


if __name__ == "__main__":
    main()
