from __future__ import annotations

import pandas as pd


BASE_COLUMNS = [
    "Id", "Time", "Wkn", "Underlying", "OptionType", "Action", "Counterparty",
    "Side", "TradePrice", "Quantity", "ContractSize", "Category", "Information",
]

CATEGORY_COLUMNS = ["Action", "Side", "Category", "OptionType", "Counterparty"]


def normalize_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            *BASE_COLUMNS,
            "IsTrade", "IsQuote", "AbsQuantity", "WknLower", "UnderlyingLower",
            "TradeValue", "TimeDisplay",
        ])

    out = df.copy()

    # Ensure expected columns exist.
    for col in BASE_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA

    out["Time"] = pd.to_datetime(out["Time"], errors="coerce")
    out["TradePrice"] = pd.to_numeric(out["TradePrice"], errors="coerce")
    out["Quantity"] = pd.to_numeric(out["Quantity"], errors="coerce").fillna(0).astype(int)
    out["ContractSize"] = pd.to_numeric(out["ContractSize"], errors="coerce").fillna(0.0)

    out["IsTrade"] = out["Action"].astype(str).eq("TradeOK")
    out["IsQuote"] = out["Action"].astype(str).eq("QuoteOK")
    out["AbsQuantity"] = out["Quantity"].abs()

    out["WknLower"] = out["Wkn"].astype(str).str.lower()
    out["UnderlyingLower"] = out["Underlying"].astype(str).str.lower()

    out["TradeValue"] = 0.0
    trade_mask = out["IsTrade"]
    out.loc[trade_mask, "TradeValue"] = (
        out.loc[trade_mask, "TradePrice"].fillna(0.0)
        * out.loc[trade_mask, "Quantity"].fillna(0.0)
    )

    # Avoid datetime formatting in hot table path.
    out["TimeDisplay"] = out["Time"].dt.strftime("%H:%M:%S").fillna("")

    # Memory/perf: categorical dtypes for low-cardinality columns.
    for col in CATEGORY_COLUMNS:
        if col in out.columns:
            out[col] = out[col].astype("category")

    return out.sort_values(["Time", "Id"], na_position="last").reset_index(drop=True)
