from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class KOTimeChart(QWidget):
    def __init__(self, title: str = "KO events over time", value_col: str = "CumKOEvents", parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(230)
        self._title = title
        self._value_col = value_col
        self._df = pd.DataFrame(columns=["BucketMin", "KOEvents", "CumKOEvents", "CumKOValue"])

    def set_data(self, df: pd.DataFrame) -> None:
        self._df = df.copy() if df is not None else pd.DataFrame(columns=["BucketMin", "KOEvents", "CumKOEvents", "CumKOValue"])
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        p.fillRect(rect, QColor("#f7fbff"))
        card = rect.adjusted(8, 8, -8, -8)
        p.setPen(QPen(QColor("#d8e7f5"), 1))
        p.setBrush(QColor("#ffffff"))
        p.drawRoundedRect(card, 16, 16)

        font = QFont(); font.setPointSize(11); font.setBold(True)
        p.setFont(font); p.setPen(QColor("#17324d"))
        p.drawText(card.adjusted(16, 10, -16, -10), Qt.AlignTop | Qt.AlignLeft, self._title)

        plot = QRectF(card.left() + 50, card.top() + 48, card.width() - 82, card.height() - 84)
        self._grid(p, plot)

        if self._df.empty:
            p.setPen(QColor("#7d8fa3"))
            p.drawText(plot, Qt.AlignCenter, "Click Call Argus")
            return

        df = self._df.sort_values("BucketMin").reset_index(drop=True)
        if self._value_col not in df.columns:
            return
        values = pd.to_numeric(df[self._value_col], errors="coerce").fillna(0).tolist()
        n = len(df)
        xs = [plot.left() + plot.width() * i / max(n - 1, 1) for i in range(n)]
        vmax = max(max(values), 1)
        ys = [plot.bottom() - v / vmax * plot.height() for v in values]

        self._line(p, xs, ys, QColor("#1864ab"), 2.2)

        small = QFont(); small.setPointSize(8)
        p.setFont(small)
        p.setPen(QColor("#1864ab"))
        p.drawText(QRectF(4, plot.top() - 8, 44, 20), Qt.AlignRight, self._fmt(vmax))
        p.drawText(QRectF(4, plot.bottom() - 10, 44, 20), Qt.AlignRight, "0")
        self._ticks(p, plot, df)

    def _fmt(self, value: float) -> str:
        if abs(value) >= 1_000_000:
            return f"{value/1_000_000:.1f}M"
        if abs(value) >= 1_000:
            return f"{value/1_000:.1f}k"
        return f"{value:.0f}"

    def _grid(self, p, plot):
        p.setPen(QPen(QColor("#e6eef7"), 1))
        for i in range(4):
            y = plot.top() + plot.height() * i / 3
            p.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
        p.setPen(QPen(QColor("#c7d7e8"), 1))
        p.drawRect(plot)

    def _line(self, p, xs, ys, color, width):
        if not xs:
            return
        path = QPainterPath(QPointF(xs[0], ys[0]))
        for x, y in zip(xs[1:], ys[1:]):
            path.lineTo(QPointF(x, y))
        p.setPen(QPen(color, width))
        p.drawPath(path)

    def _ticks(self, p, plot, df):
        mins = pd.to_numeric(df["BucketMin"], errors="coerce")
        if mins.dropna().empty:
            return
        min_m, max_m = int(mins.min()), int(mins.max())
        if max_m <= min_m:
            return
        ticks = list(range(((min_m + 59) // 60) * 60, max_m + 1, 60))
        small = QFont(); small.setPointSize(8)
        p.setFont(small); p.setPen(QColor("#6f7f90"))
        for m in ticks:
            x = plot.left() + (m - min_m) / max(max_m - min_m, 1) * plot.width()
            p.drawText(QRectF(x - 22, plot.bottom() + 6, 44, 16), Qt.AlignCenter, f"{m // 60:02d}:00")
