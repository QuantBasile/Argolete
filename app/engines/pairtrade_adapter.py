from __future__ import annotations

import pandas as pd


def compute_pair_summary(filtered_df: pd.DataFrame) -> dict:
    """Dummy placeholder for the future optimized pair-trade module."""
    if filtered_df is None or filtered_df.empty:
        return {"pnl_1m": 0.0, "pnl_3m": 0.0, "pnl_10m": 0.0, "highlight_wkns": set()}

    trade_df = filtered_df.loc[filtered_df["IsTrade"]].copy()
    top_wkns = set(trade_df["Wkn"].head(5).tolist())
    return {
        "pnl_1m": round(len(trade_df) * 0.12, 2),
        "pnl_3m": round(len(trade_df) * 0.21, 2),
        "pnl_10m": round(len(trade_df) * 0.37, 2),
        "highlight_wkns": top_wkns,
    }
