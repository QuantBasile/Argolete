from __future__ import annotations

import math
from typing import Sequence

import pandas as pd
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class DualAxisCurveWidget(QWidget):
    """Lightweight custom chart for live vs optional historic volume and trades."""

    def __init__(self, title: str = "Intraday Trade Flow", parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(240)
        self._title = title
        self._df = pd.DataFrame(columns=["BucketMin", "CumVolume", "CumTrades", "HistCumVolume", "HistCumTrades"])

    def set_title(self, title: str) -> None:
        self._title = title
        self.update()

    def set_data(self, df: pd.DataFrame) -> None:
        self._df = df.copy() if df is not None else pd.DataFrame()
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

        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor("#17324d"))
        painter.drawText(card.adjusted(16, 10, -16, -10), Qt.AlignTop | Qt.AlignLeft, self._title)

        plot = QRectF(card.left() + 58, card.top() + 48, card.width() - 116, card.height() - 86)
        self._draw_grid(painter, plot)

        if self._df.empty or len(self._df) < 2:
            painter.setPen(QColor("#7d8fa3"))
            painter.drawText(plot, Qt.AlignCenter, "No TradeOK data yet")
            return

        df = self._df.reset_index(drop=True)
        n = len(df)
        xs = [plot.left() + (plot.width() * i / max(n - 1, 1)) for i in range(n)]

        vol_live = pd.to_numeric(df.get("CumVolume"), errors="coerce")
        vol_hist = pd.to_numeric(df.get("HistCumVolume"), errors="coerce") if "HistCumVolume" in df else pd.Series(dtype=float)
        tr_live = pd.to_numeric(df.get("CumTrades"), errors="coerce")
        tr_hist = pd.to_numeric(df.get("HistCumTrades"), errors="coerce") if "HistCumTrades" in df else pd.Series(dtype=float)

        max_vol = max(float(vol_live.max(skipna=True) or 0), float(vol_hist.max(skipna=True) or 0), 1.0)
        max_tr = max(float(tr_live.max(skipna=True) or 0), float(tr_hist.max(skipna=True) or 0), 1.0)

        has_hist = (
            "HistCumVolume" in df
            and "HistCumTrades" in df
            and (vol_hist.notna().any() or tr_hist.notna().any())
        )

        if has_hist:
            self._draw_series(painter, xs, vol_hist.tolist(), max_vol, plot, QColor("#91b8d9"), dashed=True, fill=False)
            self._draw_series(painter, xs, tr_hist.tolist(), max_tr, plot, QColor("#ffc27d"), dashed=True, fill=False)

        self._draw_series(painter, xs, vol_live.tolist(), max_vol, plot, QColor("#1f77b4"), dashed=False, fill=True)
        self._draw_series(painter, xs, tr_live.tolist(), max_tr, plot, QColor("#ff7f0e"), dashed=False, fill=False)

        self._draw_axes_labels(painter, plot, max_vol, max_tr)
        self._draw_legend(painter, card, has_hist=has_hist)

    def _draw_grid(self, painter: QPainter, plot: QRectF) -> None:
        painter.setPen(QPen(QColor("#e6eef7"), 1))
        for i in range(5):
            y = plot.top() + plot.height() * i / 4
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
        for i in range(6):
            x = plot.left() + plot.width() * i / 5
            painter.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
        painter.setPen(QPen(QColor("#c7d7e8"), 1))
        painter.drawRect(plot)

    def _draw_series(self, painter: QPainter, xs: Sequence[float], values: Sequence[float], vmax: float, plot: QRectF, color: QColor, dashed: bool, fill: bool) -> None:
        points = []
        for x, v in zip(xs, values):
            if v is None or pd.isna(v):
                continue
            y = plot.bottom() - (float(v) / vmax) * plot.height()
            points.append((x, y))

        if len(points) < 2:
            return

        path = QPainterPath(QPointF(points[0][0], points[0][1]))
        for x, y in points[1:]:
            path.lineTo(QPointF(x, y))

        if fill:
            fill_path = QPainterPath(path)
            fill_path.lineTo(QPointF(points[-1][0], plot.bottom()))
            fill_path.lineTo(QPointF(points[0][0], plot.bottom()))
            fill_path.closeSubpath()
            gradient = QLinearGradient(0, plot.top(), 0, plot.bottom())
            c1 = QColor(color); c1.setAlpha(42)
            c2 = QColor(color); c2.setAlpha(0)
            gradient.setColorAt(0, c1)
            gradient.setColorAt(1, c2)
            painter.fillPath(fill_path, gradient)

        pen = QPen(color, 2.0)
        if dashed:
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawPath(path)

    def _draw_axes_labels(self, painter: QPainter, plot: QRectF, max_vol: float, max_trades: float) -> None:
        small = QFont(); small.setPointSize(8)
        painter.setFont(small)

        painter.setPen(QColor("#1f77b4"))
        painter.drawText(QRectF(10, plot.top() - 8, 46, 20), Qt.AlignRight, self._fmt_num(max_vol))
        painter.drawText(QRectF(10, plot.bottom() - 10, 46, 20), Qt.AlignRight, "0")

        painter.setPen(QColor("#ff7f0e"))
        painter.drawText(QRectF(plot.right() + 8, plot.top() - 8, 48, 20), Qt.AlignLeft, self._fmt_num(max_trades))
        painter.drawText(QRectF(plot.right() + 8, plot.bottom() - 10, 48, 20), Qt.AlignLeft, "0")

        painter.setPen(QColor("#6f7f90"))
        painter.drawText(QRectF(plot.left(), plot.bottom() + 8, plot.width(), 18), Qt.AlignCenter, "time")

    def _draw_legend(self, painter: QPainter, card, has_hist: bool) -> None:
        if has_hist:
            items = [
                ("Vol live", QColor("#1f77b4"), False),
                ("Vol hist", QColor("#91b8d9"), True),
                ("Trades live", QColor("#ff7f0e"), False),
                ("Trades hist", QColor("#ffc27d"), True),
            ]
            x = card.right() - 390
        else:
            items = [
                ("Volume", QColor("#1f77b4"), False),
                ("# Trades", QColor("#ff7f0e"), False),
            ]
            x = card.right() - 200

        y = card.top() + 18
        painter.setPen(QColor("#17324d"))
        for label, color, dashed in items:
            pen = QPen(color, 3)
            if dashed:
                pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(x, y, x + 24, y)
            painter.setPen(QColor("#17324d"))
            painter.drawText(x + 30, y + 5, label)
            x += 92

    def _fmt_num(self, value: float) -> str:
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"{value / 1_000:.1f}k"
        if math.isfinite(value):
            return f"{value:.0f}"
        return "0"
