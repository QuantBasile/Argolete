from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from app.utils.constants import HIGH_NOTIONAL_ALERT


def build_intraday_trade_curve(
    raw_df: pd.DataFrame,
    baseline_curve: pd.DataFrame | None = None,
    freq: str = "5min",
) -> pd.DataFrame:
    live_cols = ["BucketMin", "CumVolume", "CumTrades"]

    if raw_df is None or raw_df.empty:
        live = pd.DataFrame(columns=live_cols)
    else:
        trades = raw_df.loc[raw_df["IsTrade"], ["Time", "TradeValue"]].copy()
        if trades.empty:
            live = pd.DataFrame(columns=live_cols)
        else:
            trades = trades.sort_values("Time")
            bucket = pd.to_datetime(trades["Time"]).dt.floor(freq)
            trades["BucketMin"] = bucket.dt.hour * 60 + bucket.dt.minute

            live = (
                trades.groupby("BucketMin", sort=True)
                .agg(Volume=("TradeValue", "sum"), Trades=("TradeValue", "size"))
                .reset_index()
            )
            live["CumVolume"] = live["Volume"].cumsum()
            live["CumTrades"] = live["Trades"].cumsum()
            live = live[live_cols]

    if baseline_curve is None or baseline_curve.empty:
        out = live.copy()
        out["HistCumVolume"] = pd.NA
        out["HistCumTrades"] = pd.NA
    else:
        out = baseline_curve.copy()
        if live.empty:
            out["CumVolume"] = pd.NA
            out["CumTrades"] = pd.NA
        else:
            out = out.merge(live, on="BucketMin", how="left")
        out = out.sort_values("BucketMin").reset_index(drop=True)

    out["TimeLabel"] = out["BucketMin"].apply(lambda m: f"{int(m)//60:02d}:{int(m)%60:02d}" if pd.notna(m) else "")
    return out


def build_entity_trade_dashboard(raw_df: pd.DataFrame, key: str, top_n: int = 10) -> pd.DataFrame:
    columns = [key, "TradedVolume", "Trades"]
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=columns)

    trades = raw_df.loc[raw_df["IsTrade"], [key, "TradeValue"]].copy()
    if trades.empty:
        return pd.DataFrame(columns=columns)

    grouped = (
        trades.groupby(key, dropna=False)
        .agg(TradedVolume=("TradeValue", "sum"), Trades=("TradeValue", "size"))
        .reset_index()
    )

    top_volume = grouped.sort_values("TradedVolume", ascending=False).head(top_n)[key]
    top_trades = grouped.sort_values("Trades", ascending=False).head(top_n)[key]
    selected = pd.Index(top_volume).union(pd.Index(top_trades))

    out = grouped.loc[grouped[key].isin(selected)].copy()
    out = out.sort_values(["TradedVolume", "Trades"], ascending=[False, False]).reset_index(drop=True)
    return out[columns]


def build_quote_dashboard(raw_df: pd.DataFrame, key: str = "Wkn", top_n: int = 10) -> pd.DataFrame:
    columns = [key, "Quotes"]
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=columns)

    quotes = raw_df.loc[raw_df["Action"].astype(str).eq("QuoteOK"), [key]].copy()
    if quotes.empty:
        return pd.DataFrame(columns=columns)

    out = (
        quotes.groupby(key, dropna=False)
        .size()
        .sort_values(ascending=False)
        .head(top_n)
        .rename("Quotes")
        .reset_index()
    )
    return out[columns]


def build_trade_quote_conversion(raw_df: pd.DataFrame, key: str = "Underlying", top_n: int = 10) -> pd.DataFrame:
    columns = [key, "Trades", "Quotes", "TradeQuoteRatio"]
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=columns)

    grouped = raw_df.groupby(key, dropna=False).agg(
        Trades=("IsTrade", "sum"),
        Quotes=("IsQuote", "sum"),
    ).reset_index()
    grouped["TradeQuoteRatio"] = grouped["Trades"] / grouped["Quotes"].replace(0, pd.NA)
    grouped["TradeQuoteRatio"] = grouped["TradeQuoteRatio"].fillna(0.0)
    out = grouped.sort_values(["TradeQuoteRatio", "Trades"], ascending=[False, False]).head(top_n).reset_index(drop=True)
    return out[columns]


def build_pair_pnl_curve(filtered_df: pd.DataFrame, highlight_wkns: set[str], freq: str = "1min") -> pd.DataFrame:
    if filtered_df is None or filtered_df.empty or not highlight_wkns:
        return pd.DataFrame(columns=["Time", "CumPairPnl"])

    pairs = filtered_df.loc[filtered_df["IsTrade"] & filtered_df["Wkn"].isin(highlight_wkns), ["Time", "TradeValue", "Side"]].copy()
    if pairs.empty:
        return pd.DataFrame(columns=["Time", "CumPairPnl"])

    sign = pairs["Side"].astype(str).map({"Sell": 1.0, "Buy": -1.0}).fillna(0.25)
    pairs["PairPnl"] = pairs["TradeValue"].fillna(0.0) * sign * 0.0002
    pairs["Bucket"] = pd.to_datetime(pairs["Time"]).dt.floor(freq)

    out = (
        pairs.groupby("Bucket", sort=True)
        .agg(PairPnl=("PairPnl", "sum"))
        .reset_index()
    )
    out["CumPairPnl"] = out["PairPnl"].cumsum()
    out = out.rename(columns={"Bucket": "Time"})
    return out[["Time", "CumPairPnl"]]


def build_newly_active_wkns(raw_df: pd.DataFrame, now: datetime, minutes: int = 5, top_n: int = 10) -> pd.DataFrame:
    columns = ["Wkn", "Underlying", "Trades", "TradedVolume"]
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=columns)

    ts = pd.to_datetime(raw_df["Time"], errors="coerce")
    recent_mask = ts >= (now - timedelta(minutes=minutes))
    old_mask = ts < (now - timedelta(minutes=minutes))

    old_wkns = set(raw_df.loc[old_mask, "Wkn"].astype(str).unique())
    recent = raw_df.loc[recent_mask & raw_df["IsTrade"]].copy()
    if recent.empty:
        return pd.DataFrame(columns=columns)

    recent = recent.loc[~recent["Wkn"].astype(str).isin(old_wkns)]
    if recent.empty:
        return pd.DataFrame(columns=columns)

    out = recent.groupby(["Wkn", "Underlying"], dropna=False).agg(
        Trades=("IsTrade", "sum"),
        TradedVolume=("TradeValue", "sum"),
    ).reset_index()
    return out.sort_values(["TradedVolume", "Trades"], ascending=[False, False]).head(top_n).reset_index(drop=True)


def build_error_strip(raw_df: pd.DataFrame, now: datetime, minutes: int = 5) -> pd.DataFrame:
    columns = ["Metric", "Count"]
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=columns)

    ts = pd.to_datetime(raw_df["Time"], errors="coerce")
    sub = raw_df.loc[ts >= (now - timedelta(minutes=minutes))]

    metrics = [
        ("TradeError", int((sub["Action"].astype(str) == "TradeError").sum())),
        ("QuoteError", int((sub["Action"].astype(str) == "QuoteError").sum())),
        ("SoldOut", int((sub["Action"].astype(str) == "SoldOut").sum())),
        ("Unknown Side", int((sub["Side"].astype(str) == "Unknown").sum())),
        ("Bad Trade Price", int((sub["IsTrade"] & (sub["TradePrice"].isna() | (sub["TradePrice"] <= 0))).sum())),
        ("Zero Quantity", int((sub["Quantity"] == 0).sum())),
    ]
    return pd.DataFrame(metrics, columns=columns)


def build_priority_alerts(raw_df: pd.DataFrame, highlight_wkns: set[str], now: datetime, top_n: int = 12) -> pd.DataFrame:
    columns = ["Time", "Wkn", "Underlying", "Reason"]
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=columns)

    df = raw_df.copy()
    reasons = []

    pair_mask = df["Wkn"].isin(highlight_wkns) & df["IsTrade"]
    high_mask = df["IsTrade"] & (df["TradeValue"] >= HIGH_NOTIONAL_ALERT)
    err_mask = df["Action"].astype(str).isin(["TradeError", "QuoteError", "SoldOut"])
    bad_mask = df["IsTrade"] & (df["TradePrice"].isna() | (df["TradePrice"] <= 0))

    tmp = df.loc[pair_mask, ["TimeDisplay", "Wkn", "Underlying"]].copy()
    tmp["Reason"] = "Pair candidate"
    reasons.append(tmp)

    tmp = df.loc[high_mask, ["TimeDisplay", "Wkn", "Underlying"]].copy()
    tmp["Reason"] = "High notional"
    reasons.append(tmp)

    tmp = df.loc[err_mask, ["TimeDisplay", "Wkn", "Underlying", "Action"]].copy()
    tmp["Reason"] = tmp["Action"].astype(str)
    tmp = tmp.drop(columns=["Action"])
    reasons.append(tmp)

    tmp = df.loc[bad_mask, ["TimeDisplay", "Wkn", "Underlying"]].copy()
    tmp["Reason"] = "Bad TradeOK price"
    reasons.append(tmp)

    if not reasons:
        return pd.DataFrame(columns=columns)

    out = pd.concat(reasons, ignore_index=True)
    out = out.rename(columns={"TimeDisplay": "Time"})
    out = out.drop_duplicates(subset=["Time", "Wkn", "Reason"], keep="last")
    return out.tail(top_n).iloc[::-1].reset_index(drop=True)[columns]
