from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Set

import pandas as pd


@dataclass
class CursorState:
    last_time: Optional[datetime] = None
    seen_ids_at_last_time: Set[str] = field(default_factory=set)

    # Production-friendly explicit cursor state.
    last_successful_poll_time: Optional[datetime] = None
    last_event_time: Optional[datetime] = None
    last_sql_query_from: Optional[datetime] = None
    last_sql_query_to: Optional[datetime] = None
    status: str = "INIT"


@dataclass
class Filters:
    action: tuple[str, ...] = tuple()
    category: tuple[str, ...] = tuple()
    side: tuple[str, ...] = tuple()
    trader: tuple[str, ...] = tuple()
    interface: tuple[str, ...] = tuple()
    wkn_text: str = ""
    underlying_text: str = ""
    pairs_only_table: bool = False
    next_event_only: bool = False


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
    raw_df: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())
    live_df: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())
    display_df: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())
    last_raw_poll_df: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())

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

    schema_report: dict = field(default_factory=dict)
    column_availability: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())

    dashboard_cache: dict = field(default_factory=dict)
    dashboard_last_refresh_at: Optional[datetime] = None
    dashboard_poll_counter: int = 0
    dashboard_status: str = "INIT"
