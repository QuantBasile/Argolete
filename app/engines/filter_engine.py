from __future__ import annotations

import pandas as pd

from app.core.state import Filters


def apply_live_filters(df: pd.DataFrame, filters: Filters) -> pd.DataFrame:
    if df is None or df.empty:
        return df.copy()

    mask = pd.Series(True, index=df.index)

    if filters.action:
        mask &= df["Action"].isin(filters.action)

    if filters.category:
        mask &= df["Category"].isin(filters.category)

    if filters.side:
        mask &= df["Side"].isin(filters.side)

    if filters.wkn_text.strip():
        needle = filters.wkn_text.strip().lower()
        mask &= df["Wkn"].astype(str).str.lower().str.contains(needle, na=False)

    if filters.underlying_text.strip():
        needle = filters.underlying_text.strip().lower()
        mask &= df["Underlying"].astype(str).str.lower().str.contains(needle, na=False)

    out = df.loc[mask].copy()
    return out.sort_values(["Time", "Id"], ascending=[False, False]).reset_index(drop=True)
