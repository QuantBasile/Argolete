from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

from app.core.state import CursorState


class FeedInterface(ABC):
    """Abstract interface for batch loading and incremental polling."""

    @abstractmethod
    def load_history(self, start: datetime, end: datetime) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def load_today(self, start: datetime, end: datetime) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def poll_since(self, cursor: CursorState) -> tuple[pd.DataFrame, CursorState]:
        raise NotImplementedError
