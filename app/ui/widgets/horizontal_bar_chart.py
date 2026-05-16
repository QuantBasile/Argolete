from __future__ import annotations

import math

import pandas as pd
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class HorizontalBarChart(QWidget):
    """Lightweight horizontal bar chart for small top-N dashboard blocks.

    This is intentionally simple and fast:
    - expects already aggregated data
    - draws only the first `max_bars`
    - no matplotlib
    - no animations
    """

    def __init__(
        self,
        title: str,
        label_col: str,
        value_col: str,
        max_bars: int = 10,
        value_decimals: int = 0,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setMinimumHeight(235)
        self._title = title
        self._label_col = label_col
        self._value_col = value_col
        self._max_bars = max_bars
        self._value_decimals = value_decimals
        self._df = pd.DataFrame(columns=[label_col, value_col])

    def set_title(self, title: str) -> None:
        self._title = title
        self.update()

    def set_data(self, df: pd.DataFrame) -> None:
        self._df = df.copy() if df is not None else pd.DataFrame(columns=[self._label_col, self._value_col])
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

        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        p.setFont(title_font)
        p.setPen(QColor("#17324d"))
        p.drawText(card.adjusted(16, 10, -16, -10), Qt.AlignTop | Qt.AlignLeft, self._title)

        plot = QRectF(card.left() + 88, card.top() + 46, card.width() - 122, card.height() - 64)

        if self._df.empty or self._label_col not in self._df.columns or self._value_col not in self._df.columns:
            p.setPen(QColor("#7d8fa3"))
            p.drawText(plot, Qt.AlignCenter, "No data")
            return

        df = self._df[[self._label_col, self._value_col]].copy()
        df[self._value_col] = pd.to_numeric(df[self._value_col], errors="coerce").fillna(0.0)
        df = df.dropna(subset=[self._label_col]).head(self._max_bars)
        if df.empty:
            p.setPen(QColor("#7d8fa3"))
            p.drawText(plot, Qt.AlignCenter, "No data")
            return

        values = df[self._value_col].tolist()
        labels = df[self._label_col].astype(str).tolist()

        max_abs = max(max(abs(v) for v in values), 1.0)
        has_negative = any(v < 0 for v in values)
        zero_x = plot.left() + (plot.width() / 2 if has_negative else 0)
        scale_width = plot.width() / 2 if has_negative else plot.width()

        bar_slot = plot.height() / max(len(values), 1)
        bar_h = max(min(bar_slot * 0.62, 20), 7)

        small = QFont()
        small.setPointSize(8)
        p.setFont(small)

        # zero axis for positive/negative charts
        if has_negative:
            p.setPen(QPen(QColor("#cedbea"), 1))
            p.drawLine(zero_x, plot.top(), zero_x, plot.bottom())

        for i, (label, value) in enumerate(zip(labels, values)):
            y = plot.top() + i * bar_slot + (bar_slot - bar_h) / 2

            if has_negative:
                w = abs(value) / max_abs * scale_width
                if value >= 0:
                    x = zero_x
                    color = QColor("#74c0fc")
                else:
                    x = zero_x - w
                    color = QColor("#ffa8a8")
            else:
                x = plot.left()
                w = value / max_abs * plot.width()
                color = QColor("#74c0fc")

            p.setPen(Qt.NoPen)
            p.setBrush(color)
            p.drawRoundedRect(QRectF(x, y, max(w, 1.0), bar_h), 4, 4)

            p.setPen(QColor("#17324d"))
            p.drawText(QRectF(card.left() + 8, y - 2, 76, bar_h + 4), Qt.AlignRight | Qt.AlignVCenter, label[:12])

            value_txt = self._fmt_value(value)
            if value >= 0:
                vx = min(x + max(w, 1.0) + 4, card.right() - 64)
                p.drawText(QRectF(vx, y - 2, 62, bar_h + 4), Qt.AlignLeft | Qt.AlignVCenter, value_txt)
            else:
                vx = max(x - 66, card.left() + 4)
                p.drawText(QRectF(vx, y - 2, 62, bar_h + 4), Qt.AlignRight | Qt.AlignVCenter, value_txt)

    def _fmt_value(self, value: float) -> str:
        if self._value_decimals > 0:
            return f"{value:,.{self._value_decimals}f}"
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if abs(value) >= 1_000:
            return f"{value / 1_000:.1f}k"
        if math.isfinite(value):
            return f"{value:,.0f}"
        return "0"
