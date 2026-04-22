from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.detail_panel import DetailPanel
from app.ui.widgets.filter_bar import FilterBar
from app.ui.widgets.kpi_card import KpiCard
from app.ui.widgets.live_table import LiveTableView


class LiveOverviewTab(QWidget):
    run_toggled = Signal(bool)
    poll_interval_changed = Signal(int)
    filters_edited = Signal()
    apply_filters_clicked = Signal()
    reset_filters_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.run_button = QPushButton("Freeze")
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["5 s", "10 s", "20 s", "60 s"])
        self.interval_combo.setCurrentText("10 s")
        self.status_label = QLabel("Last update: -")

        self.filter_bar = FilterBar()

        self.kpi_rows = KpiCard("Rows")
        self.kpi_trades = KpiCard("Trades")
        self.kpi_quotes = KpiCard("Quotes")
        self.kpi_qty = KpiCard("Quantity")
        self.kpi_pair_1 = KpiCard("Pair PnL 1m")
        self.kpi_pair_3 = KpiCard("Pair PnL 3m")

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.run_button)
        top_bar.addWidget(QLabel("Poll"))
        top_bar.addWidget(self.interval_combo)
        top_bar.addSpacing(16)
        top_bar.addWidget(self.status_label)
        top_bar.addStretch(1)

        kpi_grid = QGridLayout()
        kpi_grid.addWidget(self.kpi_rows, 0, 0)
        kpi_grid.addWidget(self.kpi_trades, 0, 1)
        kpi_grid.addWidget(self.kpi_quotes, 0, 2)
        kpi_grid.addWidget(self.kpi_qty, 0, 3)
        kpi_grid.addWidget(self.kpi_pair_1, 1, 0)
        kpi_grid.addWidget(self.kpi_pair_3, 1, 1)

        self.live_table = LiveTableView()
        self.detail_panel = DetailPanel()

        splitter = QSplitter()
        splitter.addWidget(self.live_table)
        splitter.addWidget(self.detail_panel)
        splitter.setSizes([900, 350])

        layout = QVBoxLayout(self)
        layout.addLayout(top_bar)
        layout.addWidget(self.filter_bar)
        layout.addLayout(kpi_grid)
        layout.addWidget(splitter, 1)

        self.run_button.clicked.connect(self._on_run_button)
        self.interval_combo.currentTextChanged.connect(self._on_interval_changed)
        self.filter_bar.filters_edited.connect(self.filters_edited.emit)
        self.filter_bar.apply_clicked.connect(self.apply_filters_clicked.emit)
        self.filter_bar.reset_clicked.connect(self.reset_filters_clicked.emit)
        self.live_table.row_selected.connect(self.detail_panel.set_row)

    def _on_run_button(self) -> None:
        is_running = self.run_button.text() == "Run"
        self.run_button.setText("Freeze" if is_running else "Run")
        self.run_toggled.emit(is_running)

    def _on_interval_changed(self, text: str) -> None:
        value = int(text.split()[0]) * 1000
        self.poll_interval_changed.emit(value)

    def set_last_update(self, text: str) -> None:
        self.status_label.setText(text)

    def set_filters_apply_enabled(self, enabled: bool) -> None:
        self.filter_bar.set_apply_enabled(enabled)

    def set_pending_text(self, text: str) -> None:
        self.filter_bar.set_pending_text(text)
