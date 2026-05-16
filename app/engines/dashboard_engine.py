from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from app.utils.constants import HIGH_NOTIONAL_ALERT


def build_intraday_trade_curve(raw_df: pd.DataFrame, baseline_curve: pd.DataFrame | None = None, freq: str = "5min") -> pd.DataFrame:
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
            live = trades.groupby("BucketMin", sort=True).agg(
                Volume=("TradeValue", "sum"),
                Trades=("TradeValue", "size"),
            ).reset_index()
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

    if "BucketMin" in out.columns:
        out["TimeLabel"] = out["BucketMin"].apply(lambda m: f"{int(m)//60:02d}:{int(m)%60:02d}" if pd.notna(m) else "")
    return out


def build_agio_leaderboard(raw_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Top and floor cumulative Agio by underlying.

    We sum Agio on TradeOK rows. If later you want notional-weighted Agio,
    replace CumAgio with Agio * Quantity or Agio * TradeValue in this function only.
    """
    columns = ["Bucket", "Underlying", "CumAgio", "Trades"]
    if raw_df is None or raw_df.empty or "Agio" not in raw_df.columns:
        return pd.DataFrame(columns=columns)

    trades = raw_df.loc[raw_df["IsTrade"], ["Underlying", "Agio"]].copy()
    trades["Agio"] = pd.to_numeric(trades["Agio"], errors="coerce").fillna(0.0)
    if trades.empty:
        return pd.DataFrame(columns=columns)

    grouped = trades.groupby("Underlying", dropna=False).agg(
        CumAgio=("Agio", "sum"),
        Trades=("Agio", "size"),
    ).reset_index()

    top = grouped.sort_values("CumAgio", ascending=False).head(top_n).copy()
    top["Bucket"] = "Top 10"
    floor = grouped.sort_values("CumAgio", ascending=True).head(top_n).copy()
    floor["Bucket"] = "Floor 10"

    out = pd.concat([top, floor], ignore_index=True)
    out = out.drop_duplicates(subset=["Bucket", "Underlying"], keep="first")
    return out[columns]


def build_tradertimeout_curve(raw_df: pd.DataFrame, freq: str = "5min") -> pd.DataFrame:
    columns = ["BucketMin", "TraderTimeoutCount", "TraderTimeoutCum"]
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=columns)

    tt = raw_df.loc[raw_df["DetailedAction"].astype(str).eq("TraderTimeout"), ["Time"]].copy()
    if tt.empty:
        return pd.DataFrame(columns=columns)

    bucket = pd.to_datetime(tt["Time"]).dt.floor(freq)
    tt["BucketMin"] = bucket.dt.hour * 60 + bucket.dt.minute
    out = tt.groupby("BucketMin", sort=True).size().rename("TraderTimeoutCount").reset_index()
    out["TraderTimeoutCum"] = out["TraderTimeoutCount"].cumsum()
    return out[columns]


def build_tradertimeout_by_category(raw_df: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    columns = ["Category", "TraderTimeoutCount"]
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=columns)

    tt = raw_df.loc[raw_df["DetailedAction"].astype(str).eq("TraderTimeout"), ["Category"]].copy()
    if tt.empty:
        return pd.DataFrame(columns=columns)

    out = tt.groupby("Category", dropna=False).size().sort_values(ascending=False).head(top_n).rename("TraderTimeoutCount").reset_index()
    return out[columns]


def build_next_event_monitor(raw_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    columns = ["Underlying", "WknCount", "Trades", "TradedVolume", "NetDeltaEq"]
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=columns)

    sub = raw_df.loc[raw_df["IsNextEventIn3Days"].fillna(False)].copy()
    if sub.empty:
        return pd.DataFrame(columns=columns)

    out = sub.groupby("Underlying", dropna=False).agg(
        WknCount=("Wkn", "nunique"),
        Trades=("IsTrade", "sum"),
        TradedVolume=("TradeValue", "sum"),
        NetDeltaEq=("EquityDeltaEq", "sum"),
    ).reset_index()
    return out.sort_values(["TradedVolume", "Trades"], ascending=[False, False]).head(top_n).reset_index(drop=True)[columns]


def build_entity_trade_dashboard(raw_df: pd.DataFrame, key: str, top_n: int = 10) -> pd.DataFrame:
    columns = [key, "TradedVolume", "Trades"]
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=columns)

    trades = raw_df.loc[raw_df["IsTrade"], [key, "TradeValue"]].copy()
    if trades.empty:
        return pd.DataFrame(columns=columns)

    grouped = trades.groupby(key, dropna=False).agg(
        TradedVolume=("TradeValue", "sum"),
        Trades=("TradeValue", "size"),
    ).reset_index()

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

    out = quotes.groupby(key, dropna=False).size().sort_values(ascending=False).head(top_n).rename("Quotes").reset_index()
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
    return grouped.sort_values(["TradeQuoteRatio", "Trades"], ascending=[False, False]).head(top_n).reset_index(drop=True)[columns]


def build_pair_pnl_curve(filtered_df: pd.DataFrame, highlight_wkns: set[str], freq: str = "1min") -> pd.DataFrame:
    if filtered_df is None or filtered_df.empty or not highlight_wkns:
        return pd.DataFrame(columns=["Time", "CumPairPnl"])

    pairs = filtered_df.loc[filtered_df["IsTrade"] & filtered_df["Wkn"].isin(highlight_wkns), ["Time", "TradeValue", "Side"]].copy()
    if pairs.empty:
        return pd.DataFrame(columns=["Time", "CumPairPnl"])

    sign = pairs["Side"].astype(str).map({"Sell": 1.0, "Buy": -1.0}).fillna(0.25)
    pairs["PairPnl"] = pairs["TradeValue"].fillna(0.0) * sign * 0.0002
    pairs["Bucket"] = pd.to_datetime(pairs["Time"]).dt.floor(freq)

    out = pairs.groupby("Bucket", sort=True).agg(PairPnl=("PairPnl", "sum")).reset_index()
    out["CumPairPnl"] = out["PairPnl"].cumsum()
    return out.rename(columns={"Bucket": "Time"})[["Time", "CumPairPnl"]]


def build_newly_active_wkns(raw_df: pd.DataFrame, now: datetime, minutes: int = 5, top_n: int = 10) -> pd.DataFrame:
    columns = ["Wkn", "Underlying", "TradedVolume", "Trades"]
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(columns=columns)

    ts = pd.to_datetime(raw_df["Time"], errors="coerce")
    recent_mask = ts >= (now - timedelta(minutes=minutes))
    old_mask = ts < (now - timedelta(minutes=minutes))
    old_wkns = set(raw_df.loc[old_mask, "Wkn"].astype(str).unique())

    recent = raw_df.loc[recent_mask & raw_df["IsTrade"]].copy()
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
        ("QuoteError", int((sub["Action"].astype(str) == "QuoteError").sum())),
        ("TradeError", int((sub["Action"].astype(str) == "TradeError").sum())),
        ("QuoteRouting", int((sub["Action"].astype(str) == "QuoteRouting").sum())),
        ("TradeRouting", int((sub["Action"].astype(str) == "TradeRouting").sum())),
        ("TraderTimeout", int((sub["DetailedAction"].astype(str) == "TraderTimeout").sum())),
        ("SoldOut", int((sub["DetailedAction"].astype(str) == "SoldOut").sum())),
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

    checks = [
        (df["Wkn"].isin(highlight_wkns) & df["IsTrade"], "Pair candidate"),
        (df["IsTrade"] & (df["TradeValue"] >= HIGH_NOTIONAL_ALERT), "High notional"),
        (df["DetailedAction"].astype(str).eq("TraderTimeout"), "TraderTimeout"),
        (df["DetailedAction"].astype(str).eq("SoldOut"), "SoldOut"),
        (df["Action"].astype(str).isin(["TradeError", "QuoteError"]), "Error"),
        (df["IsNextEventIn3Days"].fillna(False), "Event<3d"),
        (df["IsTrade"] & (df["TradePrice"].isna() | (df["TradePrice"] <= 0)), "Bad TradeOK price"),
    ]

    for mask, reason in checks:
        tmp = df.loc[mask, ["TimeDisplay", "Wkn", "Underlying"]].copy()
        tmp["Reason"] = reason
        reasons.append(tmp)

    if not reasons:
        return pd.DataFrame(columns=columns)

    out = pd.concat(reasons, ignore_index=True)
    out = out.rename(columns={"TimeDisplay": "Time"})
    out = out.drop_duplicates(subset=["Time", "Wkn", "Reason"], keep="last")
    return out.tail(top_n).iloc[::-1].reset_index(drop=True)[columns]
