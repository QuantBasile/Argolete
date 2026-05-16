from __future__ import annotations

from app import config
from app.data.fake_feed import FakeFeed
from app.data.feed_interface import FeedInterface
from app.data.sql_feed import SqlFeed


def create_feed() -> FeedInterface:
    if config.DATA_SOURCE.lower() == "sql":
        return SqlFeed()
    return FakeFeed()
