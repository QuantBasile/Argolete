from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from app.ui.widgets.checkable_combo import CheckableComboBox


class FilterBar(QWidget):
    filters_edited = Signal()
    apply_clicked = Signal()
    reset_clicked = Signal()
    preset_selected = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["All", "TradeOK", "Errors", "TraderTimeout", "SoldOut", "NextEvent<3d", "MyTrader"])

        self.action_combo = CheckableComboBox(
            "Action",
            ["Info", "QuoteError", "QuoteOK", "QuoteRouting", "TradeError", "TradeOK", "TradeRouting"],
        )
        self.category_combo = CheckableComboBox(
            "Category",
            ["OpenEnd", "TurboOs", "StockOs", "RevCon", "MiniCert", "IndexOs", "DiscOs", "Other"],
        )
        self.side_combo = CheckableComboBox("Side", ["Buy", "Sell", "Unknown"])
        self.trader_combo = CheckableComboBox("Trader", ["T01", "T02", "T03", "T04", "AUTO"])
        self.interface_combo = CheckableComboBox("Interface", ["LSX", "TR", "RFQ", "OMS", "API"])

        self.wkn_edit = QLineEdit()
        self.wkn_edit.setPlaceholderText("WKN filter")
        self.underlying_edit = QLineEdit()
        self.underlying_edit.setPlaceholderText("Underlying filter")

        self.pairs_only = QCheckBox("Pairs only in table")
        self.next_event_only = QCheckBox("Event<3d")

        self.apply_button = QPushButton("Apply Filters")
        self.reset_button = QPushButton("Reset Filters")
        self.pending_label = QLabel("")
        self.summary_label = QLabel("Rows: - | Active filters: none")
        self.summary_label.setObjectName("FilterSummary")

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Preset"))
        row1.addWidget(self.preset_combo)
        row1.addWidget(QLabel("Action"))
        row1.addWidget(self.action_combo)
        row1.addWidget(QLabel("Category"))
        row1.addWidget(self.category_combo)
        row1.addWidget(QLabel("Side"))
        row1.addWidget(self.side_combo)
        row1.addStretch(1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Trader"))
        row2.addWidget(self.trader_combo)
        row2.addWidget(QLabel("Interface"))
        row2.addWidget(self.interface_combo)
        row2.addWidget(self.wkn_edit)
        row2.addWidget(self.underlying_edit)
        row2.addWidget(self.pairs_only)
        row2.addWidget(self.next_event_only)
        row2.addWidget(self.apply_button)
        row2.addWidget(self.reset_button)
        row2.addWidget(self.pending_label)
        row2.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addWidget(self.summary_label)

        self.preset_combo.currentTextChanged.connect(self.preset_selected.emit)
        self.action_combo.changed.connect(self.filters_edited.emit)
        self.category_combo.changed.connect(self.filters_edited.emit)
        self.side_combo.changed.connect(self.filters_edited.emit)
        self.trader_combo.changed.connect(self.filters_edited.emit)
        self.interface_combo.changed.connect(self.filters_edited.emit)
        self.wkn_edit.textChanged.connect(self.filters_edited.emit)
        self.underlying_edit.textChanged.connect(self.filters_edited.emit)
        self.pairs_only.stateChanged.connect(self.filters_edited.emit)
        self.next_event_only.stateChanged.connect(self.filters_edited.emit)
        self.apply_button.clicked.connect(self.apply_clicked.emit)
        self.reset_button.clicked.connect(self.reset_clicked.emit)

    def set_apply_enabled(self, enabled: bool) -> None:
        self.apply_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)

    def set_pending_text(self, text: str) -> None:
        self.pending_label.setText(text)

    def set_summary(self, text: str) -> None:
        self.summary_label.setText(text)

    def clear_all(self) -> None:
        self.action_combo.clear_checks()
        self.category_combo.clear_checks()
        self.side_combo.clear_checks()
        self.trader_combo.clear_checks()
        self.interface_combo.clear_checks()
        self.wkn_edit.clear()
        self.underlying_edit.clear()
        self.pairs_only.setChecked(False)
        self.next_event_only.setChecked(False)
