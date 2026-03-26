
"""Helpers for loading/preprocessing price data.

You can extend these with your own Alpaca/Binance pipelines.
"""

from __future__ import annotations

import pandas as pd


def load_price_csv(path: str) -> pd.DataFrame:
    """Load a CSV with at least 'close' column.

    This is just a thin wrapper so the example script stays clean.
    """

    df = pd.read_csv(path)
    if "close" not in df.columns:
        raise ValueError("CSV must include a 'close' column.")
    return df
