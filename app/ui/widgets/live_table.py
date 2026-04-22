from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QTableView

from app.utils.constants import LIVE_VISIBLE_COLUMNS


class LiveTableModel(QAbstractTableModel):
    """Simple table model backed by a pandas DataFrame."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._df = pd.DataFrame(columns=LIVE_VISIBLE_COLUMNS)
        self._highlight_wkns = set()

    def set_frame(self, df: pd.DataFrame, highlight_wkns: set[str] | None = None) -> None:
        self.beginResetModel()
        self._df = df.copy() if df is not None else pd.DataFrame(columns=LIVE_VISIBLE_COLUMNS)
        self._highlight_wkns = highlight_wkns or set()
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._df)

    def columnCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(LIVE_VISIBLE_COLUMNS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col_name = LIVE_VISIBLE_COLUMNS[index.column()]
        value = self._df.iloc[row][col_name]

        if role == Qt.DisplayRole:
            if pd.isna(value):
                return ""
            if col_name == "Time":
                try:
                    return pd.to_datetime(value).strftime("%H:%M:%S")
                except Exception:
                    return str(value)
            return str(value)

        if role == Qt.BackgroundRole:
            wkn = str(self._df.iloc[row].get("Wkn", ""))
            if wkn in self._highlight_wkns:
                return QColor("#fff3bf")

        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return LIVE_VISIBLE_COLUMNS[section]
        return str(section + 1)

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        if self._df.empty:
            return
        col_name = LIVE_VISIBLE_COLUMNS[column]
        ascending = order == Qt.AscendingOrder
        self.layoutAboutToBeChanged.emit()
        self._df = self._df.sort_values(col_name, ascending=ascending, kind="mergesort").reset_index(drop=True)
        self.layoutChanged.emit()

    def row_dict(self, row: int) -> dict:
        if row < 0 or row >= len(self._df):
            return {}
        return self._df.iloc[row].to_dict()


class LiveTableView(QTableView):
    """Fastish live table view."""

    row_selected = Signal(dict)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model_ = LiveTableModel(self)
        self.setModel(self.model_)
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.clicked.connect(self._emit_row)

    def set_data(self, df: pd.DataFrame, highlight_wkns: set[str] | None = None) -> None:
        self.model_.set_frame(df, highlight_wkns)
        self.resizeColumnsToContents()

    def _emit_row(self, index: QModelIndex) -> None:
        self.row_selected.emit(self.model_.row_dict(index.row()))
