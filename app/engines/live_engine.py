from __future__ import annotations

import pandas as pd


def merge_new_rows(existing: pd.DataFrame, new_rows: pd.DataFrame) -> pd.DataFrame:
    """Append and deduplicate by Id."""
    if existing is None or existing.empty:
        return new_rows.copy().sort_values(["Time", "Id"]).reset_index(drop=True)
    if new_rows is None or new_rows.empty:
        return existing.copy()

    out = pd.concat([existing, new_rows], ignore_index=True)
    out = out.drop_duplicates(subset=["Id"], keep="last")
    out = out.sort_values(["Time", "Id"]).reset_index(drop=True)
    return out


def compute_kpis(filtered_df: pd.DataFrame, baseline_summary: dict) -> dict:
    """Compute minimal live KPIs."""
    if filtered_df is None or filtered_df.empty:
        return {
            "rows": 0,
            "trades": 0,
            "quotes": 0,
            "quantity": 0,
            "vs_rows": 0,
            "vs_quantity": 0,
        }

    rows = int(len(filtered_df))
    trades = int(filtered_df["IsTrade"].sum())
    quotes = int(filtered_df["IsQuote"].sum())
    quantity = int(filtered_df["Quantity"].sum())

    base_rows = baseline_summary.get("avg_daily_rows", 0) or 0
    base_qty = baseline_summary.get("avg_daily_quantity", 0) or 0

    vs_rows = ((rows / base_rows - 1.0) * 100.0) if base_rows else 0.0
    vs_qty = ((quantity / base_qty - 1.0) * 100.0) if base_qty else 0.0

    return {
        "rows": rows,
        "trades": trades,
        "quotes": quotes,
        "quantity": quantity,
        "vs_rows": vs_rows,
        "vs_quantity": vs_qty,
    }
