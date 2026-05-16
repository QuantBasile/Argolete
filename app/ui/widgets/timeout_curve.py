from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class TimeoutCurveWidget(QWidget):
    """TraderTimeout count and cumulative count in 5-minute buckets."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(220)
        self._df = pd.DataFrame(columns=["BucketMin", "TraderTimeoutCount", "TraderTimeoutCum"])

    def set_data(self, df: pd.DataFrame) -> None:
        self._df = df.copy() if df is not None else pd.DataFrame(columns=["BucketMin", "TraderTimeoutCount", "TraderTimeoutCum"])
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

        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#17324d"))
        painter.drawText(card.adjusted(16, 10, -16, -10), Qt.AlignTop | Qt.AlignLeft, "TraderTimeout — 5m count + cumulative")

        plot = QRectF(card.left() + 46, card.top() + 48, card.width() - 92, card.height() - 86)
        self._draw_grid(painter, plot)

        if self._df.empty:
            painter.setPen(QColor("#7d8fa3"))
            painter.drawText(plot, Qt.AlignCenter, "No TraderTimeout")
            return

        df = self._df.sort_values("BucketMin").reset_index(drop=True)
        counts = pd.to_numeric(df["TraderTimeoutCount"], errors="coerce").fillna(0).tolist()
        cums = pd.to_numeric(df["TraderTimeoutCum"], errors="coerce").fillna(0).tolist()

        n = len(df)
        max_count = max(max(counts), 1)
        max_cum = max(max(cums), 1)

        xs = [plot.left() + plot.width() * i / max(n - 1, 1) for i in range(n)]
        y_count = [plot.bottom() - (v / max_count) * plot.height() for v in counts]
        y_cum = [plot.bottom() - (v / max_cum) * plot.height() for v in cums]

        self._draw_line(painter, xs, y_count, QColor("#d9480f"), width=2.0, dashed=False)
        for x, y in zip(xs, y_count):
            painter.setBrush(QColor("#ff922b"))
            painter.setPen(QPen(QColor("#d9480f"), 1))
            painter.drawEllipse(QPointF(x, y), 3, 3)

        self._draw_line(painter, xs, y_cum, QColor("#7b2cbf"), width=2.2, dashed=False)

        self._draw_labels(painter, plot, max_count, max_cum)
        self._draw_time_ticks(painter, plot, df)
        self._draw_legend(painter, card)

    def _draw_grid(self, painter: QPainter, plot: QRectF) -> None:
        painter.setPen(QPen(QColor("#e6eef7"), 1))
        for i in range(4):
            y = plot.top() + plot.height() * i / 3
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
        for i in range(5):
            x = plot.left() + plot.width() * i / 4
            painter.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
        painter.setPen(QPen(QColor("#c7d7e8"), 1))
        painter.drawRect(plot)

    def _draw_line(self, painter: QPainter, xs, ys, color: QColor, width: float, dashed: bool) -> None:
        if not xs:
            return
        path = QPainterPath(QPointF(xs[0], ys[0]))
        for x, y in zip(xs[1:], ys[1:]):
            path.lineTo(QPointF(x, y))
        pen = QPen(color, width)
        if dashed:
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawPath(path)

    def _draw_time_ticks(self, painter: QPainter, plot: QRectF, df: pd.DataFrame) -> None:
        if "BucketMin" not in df.columns:
            return
        mins = pd.to_numeric(df["BucketMin"], errors="coerce")
        if mins.dropna().empty:
            return

        min_m = int(mins.min())
        max_m = int(mins.max())
        if max_m <= min_m:
            return
        first_hour = ((min_m + 59) // 60) * 60
        ticks = list(range(first_hour, max_m + 1, 60))
        if not ticks:
            ticks = [min_m, max_m]

        small = QFont()
        small.setPointSize(8)
        painter.setFont(small)
        painter.setPen(QColor("#6f7f90"))
        for m in ticks:
            x = plot.left() + (m - min_m) / max(max_m - min_m, 1) * plot.width()
            painter.drawLine(QPointF(x, plot.bottom()), QPointF(x, plot.bottom() + 4))
            painter.drawText(QRectF(x - 22, plot.bottom() + 6, 44, 16), Qt.AlignCenter, f"{m // 60:02d}:00")

    def _draw_labels(self, painter: QPainter, plot: QRectF, max_count: float, max_cum: float) -> None:
        small = QFont()
        small.setPointSize(8)
        painter.setFont(small)

        painter.setPen(QColor("#d9480f"))
        painter.drawText(QRectF(4, plot.top() - 8, 40, 20), Qt.AlignRight, str(int(max_count)))
        painter.drawText(QRectF(4, plot.bottom() - 10, 40, 20), Qt.AlignRight, "0")

        painter.setPen(QColor("#7b2cbf"))
        painter.drawText(QRectF(plot.right() + 6, plot.top() - 8, 42, 20), Qt.AlignLeft, str(int(max_cum)))
        painter.drawText(QRectF(plot.right() + 6, plot.bottom() - 10, 42, 20), Qt.AlignLeft, "0")

    def _draw_legend(self, painter: QPainter, card) -> None:
        x = card.right() - 245
        y = card.top() + 18

        painter.setPen(QPen(QColor("#d9480f"), 3))
        painter.drawLine(x, y, x + 24, y)
        painter.setPen(QColor("#17324d"))
        painter.drawText(x + 30, y + 5, "5m count")

        x2 = x + 115
        painter.setPen(QPen(QColor("#7b2cbf"), 3))
        painter.drawLine(x2, y, x2 + 24, y)
        painter.setPen(QColor("#17324d"))
        painter.drawText(x2 + 30, y + 5, "cum day")
