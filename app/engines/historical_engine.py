from __future__ import annotations

from datetime import datetime

import pandas as pd


def build_baseline_summary(history_df: pd.DataFrame, now: datetime) -> dict:
    """Build a minimal frozen baseline summary from history."""
    if history_df is None or history_df.empty:
        return {
            "avg_daily_rows": 0,
            "avg_daily_trade_rows": 0,
            "avg_daily_quantity": 0,
        }

    df = history_df.copy()
    df["Date"] = pd.to_datetime(df["Time"]).dt.date
    by_day = df.groupby("Date").agg(
        rows=("Id", "count"),
        trade_rows=("Action", lambda s: s.astype(str).str.contains("Trade", case=False, na=False).sum()),
        quantity=("Quantity", "sum"),
    )
    return {
        "avg_daily_rows": int(round(by_day["rows"].mean())),
        "avg_daily_trade_rows": int(round(by_day["trade_rows"].mean())),
        "avg_daily_quantity": int(round(by_day["quantity"].mean())),
    }
