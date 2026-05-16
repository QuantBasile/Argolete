from __future__ import annotations

import random
from datetime import datetime, timedelta

import pandas as pd
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QPushButton, QScrollArea, QSplitter, QVBoxLayout, QWidget

from app.ui.widgets.dashboard_table import DashboardTable
from app.ui.widgets.horizontal_bar_chart import HorizontalBarChart
from app.ui.widgets.ko_charts import KOTimeChart


class KOArgusTab(QWidget):
    """Mock KO/Product Events tab.

    Later replace `_fake_argus_data()` with a real Argus client call.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.call_button = QPushButton("Call Argus")
        self.call_button.clicked.connect(self.call_argus)

        self.ko_table = DashboardTable(
            "KO Events",
            ["KOTime", "Wkn", "Underlying", "Category", "Side", "Quantity", "Ref1", "Strike", "KOValue", "Trader", "DistancePct"],
            {
                "KOTime": "Time",
                "Wkn": "WKN",
                "Underlying": "Underlying",
                "Category": "Category",
                "Side": "Side",
                "Quantity": "Qty",
                "Ref1": "Ref1",
                "Strike": "Strike",
                "KOValue": "KO Value",
                "Trader": "Trader",
                "DistancePct": "Dist %",
            },
        )

        self.time_chart = KOTimeChart("KO cumulative events over time", "CumKOEvents")
        self.cum_value_chart = KOTimeChart("KO cumulative value over time", "CumKOValue")
        self.underlying_chart = HorizontalBarChart("KO value by underlying", "Underlying", "KOValue", max_bars=8)
        self.category_chart = HorizontalBarChart("KO events by category", "Category", "KOEvents", max_bars=8)
        self.side_chart = HorizontalBarChart("KO value by side", "Side", "KOValue", max_bars=4)
        self.trader_chart = HorizontalBarChart("KO events by trader", "Trader", "KOEvents", max_bars=8)
        self.distance_chart = HorizontalBarChart("KO distance-to-strike buckets", "DistanceBucket", "KOEvents", max_bars=8)

        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)

        chart_grid = QGridLayout()
        chart_grid.setSpacing(10)
        chart_grid.addWidget(self.time_chart, 0, 0)
        chart_grid.addWidget(self.cum_value_chart, 0, 1)
        chart_grid.addWidget(self.underlying_chart, 1, 0)
        chart_grid.addWidget(self.category_chart, 1, 1)
        chart_grid.addWidget(self.side_chart, 2, 0)
        chart_grid.addWidget(self.trader_chart, 2, 1)
        chart_grid.addWidget(self.distance_chart, 3, 0, 1, 2)

        right_layout.addLayout(chart_grid)
        right_layout.addStretch(1)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setWidget(right_content)

        splitter = QSplitter()
        splitter.addWidget(self.ko_table)
        splitter.addWidget(right_scroll)
        splitter.setSizes([930, 720])

        top = QHBoxLayout()
        top.addWidget(self.call_button)
        top.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(splitter, 1)

    def call_argus(self) -> None:
        df = self._fake_argus_data()
        self.ko_table.set_data(df)

        curve = self._curve(df)
        self.time_chart.set_data(curve)
        self.cum_value_chart.set_data(curve)

        by_underlying = (
            df.groupby("Underlying", dropna=False)
            .agg(KOValue=("KOValue", "sum"))
            .reset_index()
            .sort_values("KOValue", ascending=False)
        )
        self.underlying_chart.set_data(by_underlying)

        by_category = (
            df.groupby("Category", dropna=False)
            .size()
            .rename("KOEvents")
            .reset_index()
            .sort_values("KOEvents", ascending=False)
        )
        self.category_chart.set_data(by_category)

        by_side = (
            df.groupby("Side", dropna=False)
            .agg(KOValue=("KOValue", "sum"))
            .reset_index()
            .sort_values("KOValue", ascending=False)
        )
        self.side_chart.set_data(by_side)

        by_trader = (
            df.groupby("Trader", dropna=False)
            .size()
            .rename("KOEvents")
            .reset_index()
            .sort_values("KOEvents", ascending=False)
        )
        self.trader_chart.set_data(by_trader)

        by_distance = (
            df.groupby("DistanceBucket", dropna=False)
            .size()
            .rename("KOEvents")
            .reset_index()
        )
        # preserve intuitive bucket order
        order = ["<0.5%", "0.5-1%", "1-2%", "2-5%", "5%+"]
        by_distance["ord"] = by_distance["DistanceBucket"].map({v: i for i, v in enumerate(order)}).fillna(99)
        by_distance = by_distance.sort_values("ord").drop(columns=["ord"])
        self.distance_chart.set_data(by_distance)

    def _fake_argus_data(self) -> pd.DataFrame:
        rnd = random.Random(123)
        underlyings = ["DAX", "Nasdaq", "SPX", "Gold", "Tesla", "Nvidia", "EuroStoxx"]
        categories = ["OpenEnd", "TurboOs", "MiniCert", "IndexOs"]
        traders = ["T01", "T02", "T03", "AUTO"]
        sides = ["Buy", "Sell"]

        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        start = now.replace(hour=8)
        rows = []
        for i in range(110):
            ts = start + timedelta(minutes=rnd.randint(0, 13 * 60))
            qty = rnd.randint(10, 5000)
            ref1 = rnd.uniform(50, 18000)
            distance = abs(rnd.gauss(0.025, 0.025))
            strike = ref1 * (1 + rnd.choice([-1, 1]) * distance)
            dist_pct = abs(ref1 - strike) / max(abs(ref1), 1e-9) * 100
            rows.append(
                {
                    "KOTime": ts.strftime("%Y-%m-%d %H:%M:%S"),
                    "Wkn": "".join(rnd.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=6)),
                    "Underlying": rnd.choice(underlyings),
                    "Category": rnd.choice(categories),
                    "Side": rnd.choice(sides),
                    "Quantity": qty,
                    "Ref1": round(ref1, 4),
                    "Strike": round(strike, 4),
                    "KOValue": round(abs(ref1 - strike) * qty * 0.01, 2),
                    "Trader": rnd.choice(traders),
                    "DistancePct": round(dist_pct, 2),
                    "DistanceBucket": self._distance_bucket(dist_pct),
                }
            )

        return pd.DataFrame(rows).sort_values("KOTime", ascending=False).reset_index(drop=True)

    def _distance_bucket(self, pct: float) -> str:
        if pct < 0.5:
            return "<0.5%"
        if pct < 1.0:
            return "0.5-1%"
        if pct < 2.0:
            return "1-2%"
        if pct < 5.0:
            return "2-5%"
        return "5%+"

    def _curve(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=["BucketMin", "KOEvents", "CumKOEvents", "CumKOValue"])
        tmp = df.copy()
        ts = pd.to_datetime(tmp["KOTime"], errors="coerce")
        bucket = ts.dt.floor("5min")
        tmp["BucketMin"] = bucket.dt.hour * 60 + bucket.dt.minute
        out = (
            tmp.groupby("BucketMin", sort=True)
            .agg(KOEvents=("Wkn", "size"), KOValue=("KOValue", "sum"))
            .reset_index()
        )
        out["CumKOEvents"] = out["KOEvents"].cumsum()
        out["CumKOValue"] = out["KOValue"].cumsum()
        return out
