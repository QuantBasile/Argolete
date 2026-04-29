from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.dashboard_table import DashboardTable
from app.ui.widgets.detail_panel import DetailPanel
from app.ui.widgets.dual_axis_curve import DualAxisCurveWidget
from app.ui.widgets.filter_bar import FilterBar
from app.ui.widgets.kpi_card import KpiCard
from app.ui.widgets.live_table import LiveTableView
from app.ui.widgets.pnl_curve import PnlCurveWidget


class LiveOverviewTab(QWidget):
    run_toggled = Signal(bool)
    poll_interval_changed = Signal(int)
    filters_edited = Signal()
    apply_filters_clicked = Signal()
    reset_filters_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.left_title = QLabel("Filtered Live Investigation")
        self.left_title.setObjectName("SectionTitle")
        self.right_title = QLabel("Unfiltered Market Pulse")
        self.right_title.setObjectName("SectionTitle")

        self.run_button = QPushButton("Freeze")
        self.mode_label = QLabel("RUNNING LIVE")
        self.mode_label.setObjectName("ModeLive")

        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["5 s", "10 s", "20 s", "60 s"])
        self.interval_combo.setCurrentText("10 s")
        self.status_label = QLabel("Last update: -")

        self.filter_bar = FilterBar()

        self.kpi_rows = KpiCard("Rows")
        self.kpi_trades = KpiCard("Trades")
        self.kpi_quotes = KpiCard("Quotes")
        self.kpi_qty = KpiCard("Quantity")
        self.kpi_traded_volume = KpiCard("Traded Volume")
        self.kpi_buy_sell_ratio = KpiCard("Buy/Sell Notional")
        self.kpi_trade_quote_ratio = KpiCard("Trade/Quote Ratio")
        self.kpi_pair_1 = KpiCard("Pair PnL 1m")

        self.live_table = LiveTableView()
        self.detail_panel = DetailPanel()

        self.pair_pnl_curve = PnlCurveWidget()
        self.filtered_flow_curve = DualAxisCurveWidget("Filtered Trade Flow")
        self.flow_curve = DualAxisCurveWidget("Unfiltered Trade Flow vs Historic")

        trade_headers = {
            "Underlying": "Underlying",
            "Wkn": "WKN",
            "Counterparty": "Counterparty",
            "TradedVolume": "Volume",
            "Trades": "# Trades",
        }
        self.tbl_underlying = DashboardTable("Top Underlyings — volume ∪ trades", ["Underlying", "TradedVolume", "Trades"], trade_headers)
        self.tbl_wkn = DashboardTable("Top WKNs — volume ∪ trades", ["Wkn", "TradedVolume", "Trades"], trade_headers)
        self.tbl_counterparty = DashboardTable("Top Counterparties — volume ∪ trades", ["Counterparty", "TradedVolume", "Trades"], trade_headers)
        self.tbl_quoted_wkn = DashboardTable("Most Quoted WKNs — QuoteOK", ["Wkn", "Quotes"], {"Wkn": "WKN", "Quotes": "# Quotes"})
        self.tbl_new_wkn = DashboardTable("Newly Active WKNs — last 5m", ["Wkn", "Underlying", "TradedVolume", "Trades"], trade_headers)
        self.tbl_conversion = DashboardTable("Trade/Quote Conversion — Underlying", ["Underlying", "Trades", "Quotes", "TradeQuoteRatio"], {"Underlying": "Underlying", "Trades": "# Trades", "Quotes": "# Quotes", "TradeQuoteRatio": "T/Q"})
        self.tbl_errors = DashboardTable("Abnormal Actions — last 5m", ["Metric", "Count"], {"Metric": "Metric", "Count": "Count"})
        self.tbl_priority = DashboardTable("Priority Alerts", ["Time", "Wkn", "Underlying", "Reason"], {"Time": "Time", "Wkn": "WKN", "Underlying": "Underlying", "Reason": "Reason"})

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.left_title)
        top_bar.addSpacing(12)
        top_bar.addWidget(self.mode_label)
        top_bar.addSpacing(12)
        top_bar.addWidget(self.run_button)
        top_bar.addWidget(QLabel("Poll"))
        top_bar.addWidget(self.interval_combo)
        top_bar.addSpacing(16)
        top_bar.addWidget(self.status_label)
        top_bar.addStretch(1)

        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(10)
        kpi_grid.addWidget(self.kpi_rows, 0, 0)
        kpi_grid.addWidget(self.kpi_trades, 0, 1)
        kpi_grid.addWidget(self.kpi_quotes, 0, 2)
        kpi_grid.addWidget(self.kpi_qty, 0, 3)
        kpi_grid.addWidget(self.kpi_traded_volume, 1, 0)
        kpi_grid.addWidget(self.kpi_buy_sell_ratio, 1, 1)
        kpi_grid.addWidget(self.kpi_trade_quote_ratio, 1, 2)
        kpi_grid.addWidget(self.kpi_pair_1, 1, 3)

        # Left side: filtered plots in the same row.
        plot_splitter = QSplitter()
        plot_splitter.addWidget(self.pair_pnl_curve)
        plot_splitter.addWidget(self.filtered_flow_curve)
        plot_splitter.setSizes([500, 620])

        lower_splitter = QSplitter()
        lower_splitter.addWidget(self.live_table)
        lower_splitter.addWidget(self.detail_panel)
        lower_splitter.setSizes([820, 310])

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.addLayout(top_bar)
        left_layout.addWidget(self.filter_bar)
        left_layout.addLayout(kpi_grid)
        left_layout.addWidget(plot_splitter)
        left_layout.addWidget(lower_splitter, 1)

        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(10)
        right_layout.addWidget(self.right_title)

        # Right side: unfiltered chart stays here, above the compact table grid.
        right_layout.addWidget(self.flow_curve)

        table_grid = QGridLayout()
        table_grid.setSpacing(10)
        table_grid.addWidget(self.tbl_priority, 0, 0)
        table_grid.addWidget(self.tbl_new_wkn, 0, 1)
        table_grid.addWidget(self.tbl_errors, 1, 0)
        table_grid.addWidget(self.tbl_conversion, 1, 1)
        table_grid.addWidget(self.tbl_underlying, 2, 0)
        table_grid.addWidget(self.tbl_wkn, 2, 1)
        table_grid.addWidget(self.tbl_counterparty, 3, 0)
        table_grid.addWidget(self.tbl_quoted_wkn, 3, 1)

        right_layout.addLayout(table_grid)
        right_layout.addStretch(1)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setWidget(right_content)

        main_splitter = QSplitter()
        main_splitter.addWidget(left)
        main_splitter.addWidget(right_scroll)
        main_splitter.setSizes([1080, 720])

        layout = QVBoxLayout(self)
        layout.addWidget(main_splitter, 1)

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

    def set_filter_summary(self, text: str) -> None:
        self.filter_bar.set_summary(text)

    def set_mode(self, running: bool) -> None:
        if running:
            self.mode_label.setText("RUNNING LIVE")
            self.mode_label.setObjectName("ModeLive")
        else:
            self.mode_label.setText("SNAPSHOT MODE")
            self.mode_label.setObjectName("ModeFrozen")
        self.mode_label.style().unpolish(self.mode_label)
        self.mode_label.style().polish(self.mode_label)
