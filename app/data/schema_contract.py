from __future__ import annotations

import pandas as pd

from app.utils.constants import FINAL_SCHEMA_COLUMNS

REQUIRED_COLUMNS = [
    "Id", "Time", "Wkn", "Underlying", "Action", "DetailedAction",
    "Side", "TradePrice", "Quantity", "Category",
]

OPTIONAL_COLUMNS = [c for c in FINAL_SCHEMA_COLUMNS if c not in REQUIRED_COLUMNS] + ["Information"]

ALLOWED_VALUES = {
    "OptionType": {"C", "P", ""},
    "Action": {"Info", "QuoteError", "QuoteOK", "QuoteOk", "QuoteRouting", "TradeError", "TradeOK", "TradeRouting", ""},
    "DetailedAction": {
        "AutoDecline", "Cancel", "ClientTimeout", "InstrumentExpired",
        "InstrumentNotActive", "InstrumentSuspended", "NoValidPrice",
        "OK_Auto", "OK_Manual", "SoldOut", "TraderTimeout", "",
    },
    "Side": {"Buy", "Sell", "Unknown", ""},
    "Category": {"OpenEnd", "TurboOs", "StockOs", "RevCon", "MiniCert", "IndexOs", "DiscOs", "Other", ""},
}

CANONICAL_RENAMES = {
    "QuoteOk": "QuoteOK",
}


def apply_canonical_values(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    out = df.copy()
    if "Action" in out.columns:
        out["Action"] = out["Action"].replace(CANONICAL_RENAMES)
    return out


def validate_schema(df: pd.DataFrame) -> dict:
    if df is None:
        return {
            "missing_required": REQUIRED_COLUMNS.copy(),
            "missing_optional": OPTIONAL_COLUMNS.copy(),
            "extra_columns": [],
            "unknown_values": {},
            "warnings": ["Input dataframe is None"],
        }

    cols = set(df.columns)
    missing_required = [c for c in REQUIRED_COLUMNS if c not in cols]
    missing_optional = [c for c in OPTIONAL_COLUMNS if c not in cols]
    expected = set(REQUIRED_COLUMNS) | set(OPTIONAL_COLUMNS)
    extra_columns = sorted(cols - expected)

    unknown_values: dict[str, list[str]] = {}
    for col, allowed in ALLOWED_VALUES.items():
        if col not in df.columns:
            continue
        values = set(df[col].fillna("").astype(str).unique())
        unknown = sorted(values - allowed)
        if unknown:
            unknown_values[col] = unknown[:20]

    warnings = []
    if missing_required:
        warnings.append("Missing required columns: " + ", ".join(missing_required))
    if missing_optional:
        warnings.append("Missing optional columns: " + ", ".join(missing_optional))
    if extra_columns:
        warnings.append("Extra columns detected: " + ", ".join(extra_columns[:20]))
    for col, values in unknown_values.items():
        warnings.append(f"Unknown values in {col}: {values}")

    return {
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "extra_columns": extra_columns,
        "unknown_values": unknown_values,
        "warnings": warnings,
    }


def build_column_availability(df: pd.DataFrame) -> pd.DataFrame:
    columns = ["Column", "Present", "NullPct", "Dtype"]
    expected = [*FINAL_SCHEMA_COLUMNS, "Information"]

    if df is None or df.empty:
        return pd.DataFrame(
            [{"Column": c, "Present": c in (df.columns if df is not None else []), "NullPct": 100.0, "Dtype": "-"} for c in expected],
            columns=columns,
        )

    rows = []
    n = max(len(df), 1)
    for col in expected:
        present = col in df.columns
        if present:
            null_pct = float(df[col].isna().sum() / n * 100.0)
            dtype = str(df[col].dtype)
        else:
            null_pct = 100.0
            dtype = "-"
        rows.append({"Column": col, "Present": present, "NullPct": null_pct, "Dtype": dtype})

    return pd.DataFrame(rows, columns=columns)
