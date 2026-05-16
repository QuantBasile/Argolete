from __future__ import annotations

import pandas as pd

from app.core.state import SanityCounters


def merge_new_rows(existing: pd.DataFrame, new_rows: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    if existing is None or existing.empty:
        out = new_rows.copy().sort_values(["Time", "Id"], na_position="last").reset_index(drop=True)
        return out, 0
    if new_rows is None or new_rows.empty:
        return existing.copy(), 0

    before = len(existing) + len(new_rows)
    out = pd.concat([existing, new_rows], ignore_index=True)
    out = out.drop_duplicates(subset=["Id"], keep="last")
    dropped = before - len(out)
    out = out.sort_values(["Time", "Id"], na_position="last").reset_index(drop=True)
    return out, int(dropped)


def compute_kpis(filtered_df: pd.DataFrame, baseline_summary: dict, total_rows: int = 0) -> dict:
    if filtered_df is None or filtered_df.empty:
        return {
            "rows": 0, "total_rows": total_rows, "trades": 0, "quotes": 0,
            "quantity": 0, "trade_volume": 0.0, "buy_sell_ratio": 0.0,
            "trade_quote_ratio": 0.0, "vs_rows": 0.0, "vs_trades": 0.0,
            "vs_quotes": 0.0, "vs_quantity": 0.0, "vs_trade_volume": 0.0,
            "vs_buy_sell_ratio": 0.0, "vs_trade_quote_ratio": 0.0,
        }

    rows = int(len(filtered_df))
    trades = int(filtered_df["IsTrade"].sum())
    quotes = int(filtered_df["IsQuote"].sum())
    quantity = int(filtered_df["Quantity"].sum())
    trade_volume = float(filtered_df["TradeValue"].sum())

    trade_mask = filtered_df["IsTrade"]
    buy_notional = float(filtered_df.loc[trade_mask & filtered_df["Side"].astype(str).eq("Buy"), "TradeValue"].sum())
    sell_notional = float(filtered_df.loc[trade_mask & filtered_df["Side"].astype(str).eq("Sell"), "TradeValue"].sum())
    buy_sell_ratio = buy_notional / sell_notional if sell_notional else 0.0
    trade_quote_ratio = trades / quotes if quotes else 0.0

    def pct(current: float, base: float) -> float:
        return ((current / base - 1.0) * 100.0) if base else 0.0

    return {
        "rows": rows,
        "total_rows": total_rows,
        "trades": trades,
        "quotes": quotes,
        "quantity": quantity,
        "trade_volume": trade_volume,
        "buy_sell_ratio": buy_sell_ratio,
        "trade_quote_ratio": trade_quote_ratio,
        "vs_rows": pct(rows, baseline_summary.get("avg_daily_rows", 0) or 0),
        "vs_trades": pct(trades, baseline_summary.get("avg_daily_trade_rows", 0) or 0),
        "vs_quotes": pct(quotes, baseline_summary.get("avg_daily_quote_rows", 0) or 0),
        "vs_quantity": pct(quantity, baseline_summary.get("avg_daily_quantity", 0) or 0),
        "vs_trade_volume": pct(trade_volume, baseline_summary.get("avg_daily_trade_volume", 0.0) or 0.0),
        "vs_buy_sell_ratio": pct(buy_sell_ratio, baseline_summary.get("avg_daily_buy_sell_ratio", 0.0) or 0.0),
        "vs_trade_quote_ratio": pct(trade_quote_ratio, baseline_summary.get("avg_daily_trade_quote_ratio", 0.0) or 0.0),
    }


def compute_sanity_counters(df: pd.DataFrame, duplicate_ids_dropped: int = 0) -> SanityCounters:
    if df is None or df.empty:
        return SanityCounters(duplicate_ids_dropped=duplicate_ids_dropped)

    invalid_trade_price = int((df["IsTrade"] & (df["TradePrice"].isna() | (df["TradePrice"] <= 0))).sum())

    return SanityCounters(
        duplicate_ids_dropped=duplicate_ids_dropped,
        missing_id=int(df["Id"].isna().sum() + (df["Id"].astype(str).str.strip() == "").sum()),
        missing_time=int(df["Time"].isna().sum()),
        missing_wkn=int(df["Wkn"].isna().sum() + (df["Wkn"].astype(str).str.strip() == "").sum()),
        invalid_trade_price=invalid_trade_price,
        zero_quantity=int((df["Quantity"] == 0).sum()),
    )
