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
    pairs_only_table: bool = False


@dataclass
class PollQuality:
    last_rows: int = 0
    last_poll_ms: float = 0.0
    total_rows: int = 0
    last_event_time: Optional[datetime] = None
    lag_seconds: float = 0.0
    status: str = "INIT"


@dataclass
class RefreshProfile:
    reason: str = "-"
    filter_ms: float = 0.0
    metrics_ms: float = 0.0
    dashboard_ms: float = 0.0
    table_ms: float = 0.0
    total_ms: float = 0.0
    slow_warning: bool = False


@dataclass
class SanityCounters:
    duplicate_ids_dropped: int = 0
    missing_id: int = 0
    missing_time: int = 0
    missing_wkn: int = 0
    invalid_trade_price: int = 0
    zero_quantity: int = 0


@dataclass
class LiveSessionState:
    # Three stores:
    # raw_df: all normalized rows currently held in memory.
    # live_df: live-analysis dataframe. Currently same shape as raw_df but kept separate for future raw/full split.
    # display_df: latest filtered/capped rows currently shown in the big table.
    raw_df: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())
    live_df: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())
    display_df: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())

    cursor: CursorState = field(default_factory=CursorState)
    active_filters: Filters = field(default_factory=Filters)
    pending_filters: Filters = field(default_factory=Filters)

    is_running: bool = True
    last_refresh_at: Optional[datetime] = None

    baseline_summary: dict = field(default_factory=dict)
    baseline_curve: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())

    poll_quality: PollQuality = field(default_factory=PollQuality)
    refresh_profile: RefreshProfile = field(default_factory=RefreshProfile)
    sanity: SanityCounters = field(default_factory=SanityCounters)

    dashboard_cache: dict = field(default_factory=dict)
    dashboard_last_refresh_at: Optional[datetime] = None
    dashboard_poll_counter: int = 0
