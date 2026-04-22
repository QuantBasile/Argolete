from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
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

        self.apply_button = QPushButton("Apply Filters")
        self.reset_button = QPushButton("Reset Filters")
        self.pending_label = QLabel("")

        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("Action"))
        layout.addWidget(self.action_combo)
        layout.addWidget(QLabel("Category"))
        layout.addWidget(self.category_combo)
        layout.addWidget(QLabel("Side"))
        layout.addWidget(self.side_combo)
        layout.addWidget(self.wkn_edit)
        layout.addWidget(self.underlying_edit)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.reset_button)
        layout.addWidget(self.pending_label)
        layout.addStretch(1)

        self.action_combo.changed.connect(self.filters_edited.emit)
        self.category_combo.changed.connect(self.filters_edited.emit)
        self.side_combo.changed.connect(self.filters_edited.emit)
        self.wkn_edit.textChanged.connect(self.filters_edited.emit)
        self.underlying_edit.textChanged.connect(self.filters_edited.emit)
        self.apply_button.clicked.connect(self.apply_clicked.emit)
        self.reset_button.clicked.connect(self.reset_clicked.emit)

    def set_apply_enabled(self, enabled: bool) -> None:
        self.apply_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)

    def set_pending_text(self, text: str) -> None:
        self.pending_label.setText(text)
