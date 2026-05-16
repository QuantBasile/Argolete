from __future__ import annotations

import pandas as pd

from app.utils.constants import HIGH_NOTIONAL_ALERT


def apply_highlighting(df: pd.DataFrame, highlight_wkns: set[str]) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    out = df.copy()
    reasons = [[] for _ in range(len(out))]
    scores = [0 for _ in range(len(out))]

    def add(mask, reason: str, score: int) -> None:
        idxs = out.index[mask].tolist()
        pos = {idx: i for i, idx in enumerate(out.index)}
        for idx in idxs:
            i = pos[idx]
            reasons[i].append(reason)
            scores[i] += score

    add(out["Wkn"].isin(highlight_wkns) & out["IsTrade"], "Pair", 100)
    add(out["DetailedAction"].astype(str).eq("TraderTimeout"), "TraderTimeout", 80)
    add(out["DetailedAction"].astype(str).eq("SoldOut"), "SoldOut", 70)
    add(out["Action"].astype(str).isin(["TradeError", "QuoteError"]), "Error", 90)
    add(out["IsNextEventIn3Days"].fillna(False), "Event<3d", 40)
    add(out["IsTrade"] & (out["TradeValue"] >= HIGH_NOTIONAL_ALERT), "HighNotional", 50)

    out["HighlightReason"] = ["; ".join(r) for r in reasons]
    out["PriorityScore"] = scores
    return out
