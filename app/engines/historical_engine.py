from __future__ import annotations

from datetime import datetime

import pandas as pd


def build_baseline_summary(history_df: pd.DataFrame, now: datetime) -> dict:
    if history_df is None or history_df.empty:
        return {
            "avg_daily_rows": 0,
            "avg_daily_trade_rows": 0,
            "avg_daily_quote_rows": 0,
            "avg_daily_quantity": 0,
            "avg_daily_trade_volume": 0.0,
            "avg_daily_buy_sell_ratio": 0.0,
            "avg_daily_trade_quote_ratio": 0.0,
        }

    df = history_df.copy()
    df["Date"] = pd.to_datetime(df["Time"]).dt.date
    df["BuyNotional"] = 0.0
    df["SellNotional"] = 0.0

    trade_mask = df["IsTrade"]
    buy_mask = trade_mask & df["Side"].astype(str).eq("Buy")
    sell_mask = trade_mask & df["Side"].astype(str).eq("Sell")
    df.loc[buy_mask, "BuyNotional"] = df.loc[buy_mask, "TradeValue"]
    df.loc[sell_mask, "SellNotional"] = df.loc[sell_mask, "TradeValue"]

    by_day = df.groupby("Date").agg(
        rows=("Id", "count"),
        trade_rows=("IsTrade", "sum"),
        quote_rows=("IsQuote", "sum"),
        quantity=("Quantity", "sum"),
        trade_volume=("TradeValue", "sum"),
        buy_notional=("BuyNotional", "sum"),
        sell_notional=("SellNotional", "sum"),
    )

    bs_ratios = by_day["buy_notional"] / by_day["sell_notional"].replace(0, pd.NA)
    bs_ratios = bs_ratios.fillna(0.0)
    tq_ratios = by_day["trade_rows"] / by_day["quote_rows"].replace(0, pd.NA)
    tq_ratios = tq_ratios.fillna(0.0)

    return {
        "avg_daily_rows": int(round(by_day["rows"].mean())),
        "avg_daily_trade_rows": int(round(by_day["trade_rows"].mean())),
        "avg_daily_quote_rows": int(round(by_day["quote_rows"].mean())),
        "avg_daily_quantity": int(round(by_day["quantity"].mean())),
        "avg_daily_trade_volume": float(by_day["trade_volume"].mean()),
        "avg_daily_buy_sell_ratio": float(bs_ratios.mean()),
        "avg_daily_trade_quote_ratio": float(tq_ratios.mean()),
    }


def build_intraday_baseline_curve(history_df: pd.DataFrame, freq: str = "5min") -> pd.DataFrame:
    if history_df is None or history_df.empty:
        return pd.DataFrame(columns=["BucketMin", "HistCumVolume", "HistCumTrades"])

    trades = history_df.loc[history_df["IsTrade"], ["Time", "TradeValue"]].copy()
    if trades.empty:
        return pd.DataFrame(columns=["BucketMin", "HistCumVolume", "HistCumTrades"])

    ts = pd.to_datetime(trades["Time"])
    trades["Date"] = ts.dt.date
    bucket = ts.dt.floor(freq)
    trades["BucketMin"] = bucket.dt.hour * 60 + bucket.dt.minute

    per_bucket = (
        trades.groupby(["Date", "BucketMin"], sort=True)
        .agg(Volume=("TradeValue", "sum"), Trades=("TradeValue", "size"))
        .reset_index()
    )
    per_bucket["CumVolume"] = per_bucket.groupby("Date")["Volume"].cumsum()
    per_bucket["CumTrades"] = per_bucket.groupby("Date")["Trades"].cumsum()

    baseline = (
        per_bucket.groupby("BucketMin", sort=True)
        .agg(HistCumVolume=("CumVolume", "mean"), HistCumTrades=("CumTrades", "mean"))
        .reset_index()
    )
    return baseline
