from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.checkable_combo import CheckableComboBox


class FilterBar(QWidget):
    filters_edited = Signal()
    apply_clicked = Signal()
    reset_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.action_combo = CheckableComboBox(
            "Action",
            ["TradeOK", "QuoteOK", "TradeError", "QuoteError", "SoldOut"],
        )
        self.category_combo = CheckableComboBox(
            "Category",
            ["OpenEnd", "Mini", "Inline", "Vanilla", "Sprint"],
        )
        self.side_combo = CheckableComboBox(
            "Side",
            ["Buy", "Sell", "Unknown"],
        )

        self.wkn_edit = QLineEdit()
        self.wkn_edit.setPlaceholderText("WKN filter")

        self.underlying_edit = QLineEdit()
        self.underlying_edit.setPlaceholderText("Underlying filter")

        self.pairs_only = QCheckBox("Pairs only in table")

        self.apply_button = QPushButton("Apply Filters")
        self.reset_button = QPushButton("Reset Filters")
        self.pending_label = QLabel("")
        self.summary_label = QLabel("Rows: - | Active filters: none")
        self.summary_label.setObjectName("FilterSummary")

        row = QHBoxLayout()
        row.addWidget(QLabel("Action"))
        row.addWidget(self.action_combo)
        row.addWidget(QLabel("Category"))
        row.addWidget(self.category_combo)
        row.addWidget(QLabel("Side"))
        row.addWidget(self.side_combo)
        row.addWidget(self.wkn_edit)
        row.addWidget(self.underlying_edit)
        row.addWidget(self.pairs_only)
        row.addWidget(self.apply_button)
        row.addWidget(self.reset_button)
        row.addWidget(self.pending_label)
        row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(row)
        layout.addWidget(self.summary_label)

        self.action_combo.changed.connect(self.filters_edited.emit)
        self.category_combo.changed.connect(self.filters_edited.emit)
        self.side_combo.changed.connect(self.filters_edited.emit)
        self.wkn_edit.textChanged.connect(self.filters_edited.emit)
        self.underlying_edit.textChanged.connect(self.filters_edited.emit)
        self.pairs_only.stateChanged.connect(self.filters_edited.emit)
        self.apply_button.clicked.connect(self.apply_clicked.emit)
        self.reset_button.clicked.connect(self.reset_clicked.emit)

    def set_apply_enabled(self, enabled: bool) -> None:
        self.apply_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)

    def set_pending_text(self, text: str) -> None:
        self.pending_label.setText(text)

    def set_summary(self, text: str) -> None:
        self.summary_label.setText(text)
