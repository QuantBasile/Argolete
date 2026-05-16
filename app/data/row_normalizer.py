from __future__ import annotations

import pandas as pd

from app.data.schema_contract import apply_canonical_values
from app.utils.constants import FINAL_SCHEMA_COLUMNS


CATEGORY_COLUMNS = [
    "Action", "DetailedAction", "Side", "Category", "OptionType",
    "Counterparty", "Interface", "Trader",
]


def normalize_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            *FINAL_SCHEMA_COLUMNS, "Information", "IsTrade", "IsQuote",
            "AbsQuantity", "WknLower", "UnderlyingLower", "TradeValue",
            "TimeDisplay", "HighlightReason", "PriorityScore",
        ])

    out = apply_canonical_values(df.copy())

    for col in FINAL_SCHEMA_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    if "Information" not in out.columns:
        out["Information"] = ""

    out["Time"] = pd.to_datetime(out["Time"], errors="coerce")
    for col in ["Strike", "TradePrice", "ContractSize", "Ref1", "Agio", "EquityDeltaEq"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["Quantity"] = pd.to_numeric(out["Quantity"], errors="coerce").fillna(0).astype(int)
    out["ContractSize"] = out["ContractSize"].fillna(0.0)
    out["EquityDeltaEq"] = out["EquityDeltaEq"].fillna(0.0)

    out["IsNextEventIn3Days"] = (
        out["IsNextEventIn3Days"].fillna(False).astype(str).str.lower().isin(["true", "1", "yes", "y"])
    )

    out["IsTrade"] = out["Action"].astype(str).eq("TradeOK")
    out["IsQuote"] = out["Action"].astype(str).eq("QuoteOK")
    out["AbsQuantity"] = out["Quantity"].abs()
    out["WknLower"] = out["Wkn"].fillna("").astype(str).str.lower()
    out["UnderlyingLower"] = out["Underlying"].fillna("").astype(str).str.lower()

    out["TradeValue"] = 0.0
    trade_mask = out["IsTrade"]
    out.loc[trade_mask, "TradeValue"] = (
        out.loc[trade_mask, "TradePrice"].fillna(0.0)
        * out.loc[trade_mask, "Quantity"].fillna(0.0)
    )

    out["TimeDisplay"] = out["Time"].dt.strftime("%H:%M:%S").fillna("")
    out["HighlightReason"] = ""
    out["PriorityScore"] = 0

    for col in CATEGORY_COLUMNS:
        if col in out.columns:
            out[col] = out[col].fillna("").astype("category")

    return out.sort_values(["Time", "Id"], na_position="last").reset_index(drop=True)
