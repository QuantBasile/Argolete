from __future__ import annotations

import pandas as pd


def normalize_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize types and derive helper columns."""
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            "Id", "Time", "Wkn", "Underlying", "OptionType", "Action", "Counterparty",
            "Side", "TradePrice", "Quantity", "ContractSize", "Category", "Information",
            "IsTrade", "IsQuote", "AbsQuantity", "TextBlob",
        ])

    out = df.copy()
    out["Time"] = pd.to_datetime(out["Time"])
    out["TradePrice"] = pd.to_numeric(out["TradePrice"], errors="coerce")
    out["Quantity"] = pd.to_numeric(out["Quantity"], errors="coerce").fillna(0).astype(int)
    out["ContractSize"] = pd.to_numeric(out["ContractSize"], errors="coerce").fillna(0.0)
    out["IsTrade"] = out["Action"].astype(str).str.contains("Trade", case=False, na=False)
    out["IsQuote"] = out["Action"].astype(str).str.contains("Quote", case=False, na=False)
    out["AbsQuantity"] = out["Quantity"].abs()
    out["TextBlob"] = (
        out["Wkn"].astype(str).str.lower()
        + " "
        + out["Underlying"].astype(str).str.lower()
    )
    return out.sort_values(["Time", "Id"]).reset_index(drop=True)
