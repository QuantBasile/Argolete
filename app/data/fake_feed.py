from __future__ import annotations

import random
import string
from datetime import datetime, timedelta
from typing import List

import pandas as pd

from app.core.state import CursorState
from app.data.feed_interface import FeedInterface
from app.utils.constants import FINAL_SCHEMA_COLUMNS, START_HOUR


class FakeFeed(FeedInterface):
    """Fake event source simulating production-like trading logs."""

    ACTIONS = ["Info", "QuoteError", "QuoteOK", "QuoteRouting", "TradeError", "TradeOK", "TradeRouting"]
    DETAILED_ACTIONS = [
        "AutoDecline", "Cancel", "ClientTimeout", "InstrumentExpired",
        "InstrumentNotActive", "InstrumentSuspended", "NoValidPrice",
        "OK_Auto", "OK_Manual", "SoldOut", "TraderTimeout",
    ]
    SIDES = ["Buy", "Sell", "Unknown"]
    CATEGORIES = ["OpenEnd", "TurboOs", "StockOs", "RevCon", "MiniCert", "IndexOs", "DiscOs", "Other"]
    OPTION_TYPES = ["C", "P"]
    UNDERLYINGS = ["Nasdaq", "DAX", "SPX", "EuroStoxx", "Nikkei", "Gold", "Tesla", "Nvidia"]
    COUNTERPARTIES = ["BNP", "SG", "CITI", "JPM", "MS", "UBS", "Retail", "FlowDesk"]
    INTERFACES = ["LSX", "TR", "RFQ", "OMS", "API"]
    TRADERS = ["T01", "T02", "T03", "T04", "AUTO"]

    def __init__(self, seed: int = 42) -> None:
        self.random = random.Random(seed)
        self.now = datetime.now().replace(microsecond=0)
        self.master_today = self._generate_day(
            start=self.now.replace(hour=START_HOUR, minute=0, second=0, microsecond=0),
            end=self.now,
            min_rows=1200,
            max_rows=2200,
        )
        self.future_cursor = self.now

    def _random_id(self) -> str:
        return "".join(self.random.choices(string.ascii_uppercase + string.digits, k=10))

    def _random_wkn(self) -> str:
        return "".join(self.random.choices(string.ascii_uppercase + string.digits, k=6))

    def _random_isin(self) -> str:
        return "DE" + "".join(self.random.choices(string.ascii_uppercase + string.digits, k=10))

    def _random_expiry(self) -> str:
        if self.random.random() < 0.45:
            return "OpenEnd"
        days = self.random.choice([3, 7, 14, 30, 90, 180, 365])
        return (datetime.now().date() + timedelta(days=days)).isoformat()

    def _build_row(self, ts: datetime) -> dict:
        action = self.random.choices(
            self.ACTIONS,
            weights=[4, 4, 32, 8, 3, 44, 5],
            k=1,
        )[0]

        if action == "TradeOK":
            detailed = self.random.choices(["OK_Auto", "OK_Manual"], weights=[85, 15], k=1)[0]
        elif action == "QuoteOK":
            detailed = self.random.choices(["OK_Auto", "OK_Manual", "TraderTimeout"], weights=[92, 5, 3], k=1)[0]
        elif action in {"QuoteError", "TradeError"}:
            detailed = self.random.choice(["NoValidPrice", "TraderTimeout", "ClientTimeout", "AutoDecline"])
        elif action == "Info":
            detailed = self.random.choice(["InstrumentSuspended", "InstrumentExpired", "InstrumentNotActive"])
        else:
            detailed = self.random.choice(self.DETAILED_ACTIONS)

        qty = self.random.randint(10, 5000) if action == "TradeOK" else self.random.randint(0, 1000)
        price = round(self.random.uniform(0.05, 15.0), 4) if action == "TradeOK" else None
        ref1 = round(self.random.uniform(50, 18000), 4)
        underlying = self.random.choice(self.UNDERLYINGS) if self.random.random() > 0.005 else ""

        return {
            "Id": self._random_id(),
            "OptionType": self.random.choice(self.OPTION_TYPES),
            "Time": ts,
            "Interface": self.random.choice(self.INTERFACES),
            "Wkn": self._random_wkn() if self.random.random() > 0.005 else None,
            "Underlying": underlying,
            "UnderlyingIsin": self._random_isin(),
            "UnderlyingNode": f"/{underlying}/node/{self.random.randint(1, 20)}" if underlying else "",
            "Strike": round(self.random.uniform(10, 20000), 4),
            "Expiry": self._random_expiry(),
            "Action": action,
            "DetailedAction": detailed,
            "Counterparty": self.random.choice(self.COUNTERPARTIES),
            "Side": self.random.choice(self.SIDES),
            "TradePrice": price,
            "Quantity": qty,
            "ContractSize": round(self.random.choice([0.01, 0.1, 1.0]), 2),
            "Ref1": ref1,
            "Trader": self.random.choice(self.TRADERS),
            "Agio": round(self.random.uniform(-0.05, 0.25), 4) if action == "TradeOK" else None,
            "Category": self.random.choice(self.CATEGORIES),
            "EquityDeltaEq": round(self.random.uniform(-5000, 5000), 2) if action == "TradeOK" else 0.0,
            "IsNextEventIn3Days": self.random.random() < 0.08,
            "Information": "" if action in {"TradeOK", "QuoteOK"} else detailed,
        }

    def _empty_df(self) -> pd.DataFrame:
        return pd.DataFrame(columns=[*FINAL_SCHEMA_COLUMNS, "Information"])

    def _generate_day(self, start: datetime, end: datetime, min_rows: int, max_rows: int) -> pd.DataFrame:
        if end <= start:
            return self._empty_df()

        total_seconds = max(int((end - start).total_seconds()), 1)
        n = self.random.randint(min_rows, max_rows)
        seconds = sorted(self.random.randint(0, total_seconds) for _ in range(n))
        rows = [self._build_row(start + timedelta(seconds=s)) for s in seconds]
        return pd.DataFrame(rows).sort_values(["Time", "Id"]).reset_index(drop=True)

    def load_history(self, start: datetime, end: datetime) -> pd.DataFrame:
        days = pd.date_range(start=start.date(), end=end.date(), freq="D")
        parts: List[pd.DataFrame] = []
        for day in days:
            d0 = datetime.combine(day.date(), datetime.min.time()).replace(hour=START_HOUR)
            d1 = d0.replace(hour=22, minute=0)
            parts.append(self._generate_day(d0, d1, 700, 1400))
        if not parts:
            return self._empty_df()
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
