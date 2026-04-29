from __future__ import annotations

import math
from typing import Sequence

import pandas as pd
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class PnlCurveWidget(QWidget):
    """Lightweight filtered pair PnL curve."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(160)
        self._df = pd.DataFrame(columns=["Time", "CumPairPnl"])

    def set_data(self, df: pd.DataFrame) -> None:
        self._df = df.copy() if df is not None else pd.DataFrame(columns=["Time", "CumPairPnl"])
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        painter.fillRect(rect, QColor("#f7fbff"))
        card = rect.adjusted(8, 8, -8, -8)

        painter.setPen(QPen(QColor("#d8e7f5"), 1))
        painter.setBrush(QColor("#ffffff"))
        painter.drawRoundedRect(card, 16, 16)

        font = QFont(); font.setPointSize(11); font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#17324d"))
        painter.drawText(card.adjusted(16, 8, -16, -8), Qt.AlignTop | Qt.AlignLeft, "Pair PnL 1m — filtered")

        plot = QRectF(card.left() + 52, card.top() + 38, card.width() - 76, card.height() - 60)
        self._draw_grid(painter, plot)

        if self._df.empty or len(self._df) < 2:
            painter.setPen(QColor("#7d8fa3"))
            painter.drawText(plot, Qt.AlignCenter, "No pair PnL data")
            return

        values = pd.to_numeric(self._df["CumPairPnl"], errors="coerce").fillna(0.0).tolist()
        max_abs = max(max(abs(v) for v in values), 1.0)
        n = len(values)
        xs = [plot.left() + plot.width() * i / max(n - 1, 1) for i in range(n)]
        mid_y = plot.center().y()
        ys = [mid_y - (v / max_abs) * (plot.height() / 2.0) for v in values]

        path = QPainterPath(QPointF(xs[0], ys[0]))
        for x, y in zip(xs[1:], ys[1:]):
            path.lineTo(QPointF(x, y))

        painter.setPen(QPen(QColor("#7b2cbf"), 2.2))
        painter.drawPath(path)

        painter.setPen(QPen(QColor("#ccd8e5"), 1, Qt.DashLine))
        painter.drawLine(QPointF(plot.left(), mid_y), QPointF(plot.right(), mid_y))

        small = QFont(); small.setPointSize(8)
        painter.setFont(small)
        painter.setPen(QColor("#7b2cbf"))
        painter.drawText(QRectF(8, plot.top() - 8, 42, 20), Qt.AlignRight, self._fmt(max_abs))
        painter.drawText(QRectF(8, plot.bottom() - 10, 42, 20), Qt.AlignRight, self._fmt(-max_abs))

    def _draw_grid(self, painter: QPainter, plot: QRectF) -> None:
        painter.setPen(QPen(QColor("#e6eef7"), 1))
        for i in range(4):
            y = plot.top() + plot.height() * i / 3
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
        painter.setPen(QPen(QColor("#c7d7e8"), 1))
        painter.drawRect(plot)

    def _fmt(self, value: float) -> str:
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if abs(value) >= 1_000:
            return f"{value / 1_000:.1f}k"
        if math.isfinite(value):
            return f"{value:.0f}"
        return "0"
