from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Set

import pandas as pd


@dataclass
class CursorState:
    last_time: Optional[datetime] = None
    seen_ids_at_last_time: Set[str] = field(default_factory=set)


@dataclass
class Filters:
    action: tuple[str, ...] = tuple()
    category: tuple[str, ...] = tuple()
    side: tuple[str, ...] = tuple()
    wkn_text: str = ""
    underlying_text: str = ""


@dataclass
class LiveSessionState:
    raw_df: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())
    cursor: CursorState = field(default_factory=CursorState)
    active_filters: Filters = field(default_factory=Filters)
    pending_filters: Filters = field(default_factory=Filters)
    is_running: bool = True
    last_refresh_at: Optional[datetime] = None
    baseline_summary: dict = field(default_factory=dict)
