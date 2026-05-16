from __future__ import annotations

from datetime import datetime

import pandas as pd

from app.core.state import CursorState
from app.data.feed_interface import FeedInterface


class SqlFeed(FeedInterface):
    """Production SQL feed placeholder.

    Plug your existing SQLAlchemy module here. Keep this interface stable:
    - load_history(start, end) -> DataFrame
    - load_today(start, end) -> DataFrame
    - poll_since(cursor) -> (DataFrame, CursorState)

    The app expects raw rows. Normalization/validation happens after this layer.
    """

    def __init__(self) -> None:
        # TODO: initialize your SQLAlchemy engine or inject your existing SQL reader here.
        pass

    def load_history(self, start: datetime, end: datetime) -> pd.DataFrame:
        # TODO: replace with your batch SQL query.
        return pd.DataFrame()

    def load_today(self, start: datetime, end: datetime) -> pd.DataFrame:
        # TODO: replace with your batch SQL query.
        return pd.DataFrame()

    def poll_since(self, cursor: CursorState) -> tuple[pd.DataFrame, CursorState]:
        # TODO:
        # query_from = cursor.last_event_time - SQL_PUFFER_SECONDS
        # query_to = now
        # deduplication happens later by Id
        new_cursor = CursorState(
            last_time=cursor.last_time,
            seen_ids_at_last_time=set(cursor.seen_ids_at_last_time),
            last_successful_poll_time=datetime.now(),
            last_event_time=cursor.last_event_time,
            last_sql_query_from=cursor.last_sql_query_from,
            last_sql_query_to=datetime.now(),
            status="SQL_PLACEHOLDER",
        )
        return pd.DataFrame(), new_cursor
