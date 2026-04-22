from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLabel, QWidget

from app.utils.constants import DETAIL_COLUMN_ORDER


class DetailPanel(QWidget):
    """Display all selected-row details."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._labels = {}

        layout = QFormLayout(self)
        for col in DETAIL_COLUMN_ORDER:
            label = QLabel("-")
            self._labels[col] = label
            layout.addRow(col, label)

    def set_row(self, row: dict | None) -> None:
        if not row:
            for lbl in self._labels.values():
                lbl.setText("-")
            return

        for key, label in self._labels.items():
            value = row.get(key, "")
            label.setText("" if value is None else str(value))
