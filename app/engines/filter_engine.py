from __future__ import annotations

import pandas as pd

from app.core.state import Filters


def apply_live_filters(df: pd.DataFrame, filters: Filters) -> pd.DataFrame:
    if df is None or df.empty:
        return df.copy()

    mask = pd.Series(True, index=df.index)

    if filters.action:
        mask &= df["Action"].astype(str).isin(filters.action)

    if filters.category:
        mask &= df["Category"].astype(str).isin(filters.category)

    if filters.side:
        mask &= df["Side"].astype(str).isin(filters.side)

    if filters.wkn_text.strip():
        mask &= df["WknLower"].str.contains(
            filters.wkn_text.strip().lower(),
            na=False,
            regex=False,
        )

    if filters.underlying_text.strip():
        mask &= df["UnderlyingLower"].str.contains(
            filters.underlying_text.strip().lower(),
            na=False,
            regex=False,
        )

    return df.loc[mask].sort_values(["Time", "Id"], ascending=[False, False], na_position="last")


def active_filter_summary(filters: Filters, total_rows: int, filtered_rows: int) -> str:
    parts: list[str] = []

    if filters.action:
        parts.append("Action=" + ",".join(filters.action))
    if filters.category:
        parts.append("Category=" + ",".join(filters.category))
    if filters.side:
        parts.append("Side=" + ",".join(filters.side))
    if filters.wkn_text.strip():
        parts.append(f'WKN contains "{filters.wkn_text.strip()}"')
    if filters.underlying_text.strip():
        parts.append(f'Underlying contains "{filters.underlying_text.strip()}"')
    if filters.pairs_only_table:
        parts.append("Pairs only in table")

    base = f"Rows: {filtered_rows:,} filtered / {total_rows:,} raw"
    if not parts:
        return f"{base} | Active filters: none"
    return f"{base} | Active filters: " + " | ".join(parts)
