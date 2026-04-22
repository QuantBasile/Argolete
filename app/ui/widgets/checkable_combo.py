from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QComboBox


class CheckableComboBox(QComboBox):
    changed = Signal()

    def __init__(self, placeholder: str, items: list[str], parent=None) -> None:
        super().__init__(parent)
        self._placeholder = placeholder
        model = QStandardItemModel(self)
        self.setModel(model)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText(placeholder)

        for text in items:
            item = QStandardItem(text)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setData(Qt.Unchecked, Qt.CheckStateRole)
            model.appendRow(item)

        model.itemChanged.connect(self._on_item_changed)
        self._refresh_text()

    def checked_items(self) -> list[str]:
        out = []
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item.checkState() == Qt.Checked:
                out.append(item.text())
        return out

    def clear_checks(self) -> None:
        model = self.model()
        for i in range(model.rowCount()):
            model.item(i).setCheckState(Qt.Unchecked)
        self._refresh_text()
        self.changed.emit()

    def _on_item_changed(self, _item) -> None:
        self._refresh_text()
        self.changed.emit()

    def _refresh_text(self) -> None:
        checked = self.checked_items()
        if not checked:
            text = "All"
        elif len(checked) <= 2:
            text = ", ".join(checked)
        else:
            text = f"{len(checked)} selected"
        self.lineEdit().setText(text)
