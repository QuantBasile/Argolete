from __future__ import annotations

import random
import string
from datetime import datetime, timedelta
from typing import List

import pandas as pd

from app.core.state import CursorState
from app.data.feed_interface import FeedInterface
from app.utils.constants import START_HOUR


class FakeFeed(FeedInterface):
    """Fake event source simulating history, startup load, and live polling."""

    ACTIONS = ["TradeOK", "QuoteOK", "TradeError", "QuoteError", "SoldOut"]
    SIDES = ["Buy", "Sell", "Unknown"]
    CATEGORIES = ["OpenEnd", "Mini", "Inline", "Vanilla", "Sprint"]
    OPTION_TYPES = ["C", "P"]
    UNDERLYINGS = ["Nasdaq", "DAX", "SPX", "EuroStoxx", "Nikkei", "Gold", "Tesla", "Nvidia"]
    COUNTERPARTIES = ["BNP", "SG", "CITI", "JPM", "MS", "UBS", "Retail", "FlowDesk"]

    def __init__(self, seed: int = 42) -> None:
        self.random = random.Random(seed)
        self.now = self._aligned_now()
        self.master_today = self._generate_day(
            start=self.now.replace(hour=START_HOUR, minute=0, second=0, microsecond=0),
            end=self.now,
            min_rows=1200,
            max_rows=2200,
        )
        self.future_cursor = self.now

    def _aligned_now(self) -> datetime:
        now = datetime.now().replace(microsecond=0)
        return now

    def _random_id(self) -> str:
        chars = string.ascii_uppercase + string.digits
        return "".join(self.random.choices(chars, k=10))

    def _random_wkn(self) -> str:
        chars = string.ascii_uppercase + string.digits
        return "".join(self.random.choices(chars, k=6))

    def _build_row(self, ts: datetime) -> dict:
        action = self.random.choices(
            self.ACTIONS,
            weights=[50, 35, 4, 6, 5],
            k=1,
        )[0]
        qty = self.random.randint(10, 5000) if "Trade" in action else self.random.randint(1, 1000)
        trade_price = round(self.random.uniform(0.05, 15.0), 4) if "TradeOK" in action else None
        info = "" if action in {"TradeOK", "QuoteOK"} else action

        return {
            "Id": self._random_id(),
            "Time": ts,
            "Wkn": self._random_wkn(),
            "Underlying": self.random.choice(self.UNDERLYINGS),
            "OptionType": self.random.choice(self.OPTION_TYPES),
            "Action": action,
            "Counterparty": self.random.choice(self.COUNTERPARTIES),
            "Side": self.random.choice(self.SIDES),
            "TradePrice": trade_price,
            "Quantity": qty,
            "ContractSize": round(self.random.choice([0.01, 0.1, 1.0]), 2),
            "Category": self.random.choice(self.CATEGORIES),
            "Information": info,
        }

    def _generate_day(self, start: datetime, end: datetime, min_rows: int, max_rows: int) -> pd.DataFrame:
        if end <= start:
            return pd.DataFrame(columns=[
                "Id", "Time", "Wkn", "Underlying", "OptionType", "Action", "Counterparty",
                "Side", "TradePrice", "Quantity", "ContractSize", "Category", "Information"
            ])

        total_seconds = max(int((end - start).total_seconds()), 1)
        n = self.random.randint(min_rows, max_rows)
        seconds = sorted(self.random.randint(0, total_seconds) for _ in range(n))
        rows = [self._build_row(start + timedelta(seconds=s)) for s in seconds]
        df = pd.DataFrame(rows).sort_values(["Time", "Id"]).reset_index(drop=True)
        return df

    def load_history(self, start: datetime, end: datetime) -> pd.DataFrame:
        days = pd.date_range(start=start.date(), end=end.date(), freq="D")
        parts: List[pd.DataFrame] = []
        for day in days:
            d0 = datetime.combine(day.date(), datetime.min.time()).replace(hour=START_HOUR)
            d1 = d0.replace(hour=22, minute=0)
            parts.append(self._generate_day(d0, d1, 700, 1400))
        if not parts:
            return pd.DataFrame()
        return pd.concat(parts, ignore_index=True)

    def load_today(self, start: datetime, end: datetime) -> pd.DataFrame:
        mask = (self.master_today["Time"] >= start) & (self.master_today["Time"] <= end)
        return self.master_today.loc[mask].copy().reset_index(drop=True)

    def poll_since(self, cursor: CursorState) -> tuple[pd.DataFrame, CursorState]:
        batch_size = self.random.randint(8, 30)
        rows = []
        for _ in range(batch_size):
            self.future_cursor += timedelta(seconds=self.random.randint(1, 7))
            rows.append(self._build_row(self.future_cursor))

        df = pd.DataFrame(rows).sort_values(["Time", "Id"]).reset_index(drop=True)

        new_cursor = CursorState()
        if not df.empty:
            last_time = df.iloc[-1]["Time"]
            new_cursor.last_time = last_time.to_pydatetime() if hasattr(last_time, "to_pydatetime") else last_time
            ids = df.loc[df["Time"] == last_time, "Id"].tolist()
            new_cursor.seen_ids_at_last_time = set(ids)
        return df, new_cursor
