from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QHeaderView, QTableView, QToolTip

from app.utils.column_registry import COLUMN_REGISTRY, LIVE_TABLE_COLUMNS


class LiveTableModel(QAbstractTableModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._df = pd.DataFrame(columns=LIVE_TABLE_COLUMNS)
        self._records: list[dict] = []
        self._highlight_wkns = set()

    def set_frame(self, df: pd.DataFrame, highlight_wkns: set[str] | None = None) -> None:
        self.beginResetModel()
        if df is None or df.empty:
            self._df = pd.DataFrame(columns=LIVE_TABLE_COLUMNS)
        else:
            cols = [c for c in LIVE_TABLE_COLUMNS if c in df.columns]
            self._df = df.loc[:, cols].copy()
            for col in LIVE_TABLE_COLUMNS:
                if col not in self._df.columns:
                    self._df[col] = ""
            self._df = self._df[LIVE_TABLE_COLUMNS]
        self._records = self._df.to_dict("records") if not self._df.empty else []
        self._highlight_wkns = highlight_wkns or set()
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._records)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(LIVE_TABLE_COLUMNS)

    def display_value(self, row: int, column: int) -> str:
        if row < 0 or row >= len(self._records):
            return ""
        col_name = LIVE_TABLE_COLUMNS[column]
        value = self._records[row].get(col_name, "")
        if value is None or pd.isna(value):
            return ""

        fmt = COLUMN_REGISTRY.get(col_name, {}).get("format", "text")
        try:
            if fmt == "int":
                return f"{int(float(value)):,}"
            if fmt == "price":
                return f"{float(value):.4f}"
            if fmt == "float":
                return f"{float(value):.4f}"
        except Exception:
            return str(value)

        return str(value)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            return self.display_value(index.row(), index.column())

        if role == Qt.BackgroundRole:
            rec = self._records[index.row()]
            if str(rec.get("Wkn", "")) in self._highlight_wkns:
                return QColor("#fff3bf")

        if role == Qt.TextAlignmentRole:
            col = LIVE_TABLE_COLUMNS[index.column()]
            if COLUMN_REGISTRY.get(col, {}).get("format") in {"int", "price", "float"}:
                return Qt.AlignRight | Qt.AlignVCenter

        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            col = LIVE_TABLE_COLUMNS[section]
            return COLUMN_REGISTRY.get(col, {}).get("label", col)
        return str(section + 1)

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        if self._df.empty:
            return

        col_name = LIVE_TABLE_COLUMNS[column]
        ascending = order == Qt.AscendingOrder

        self.layoutAboutToBeChanged.emit()
        self._df = self._df.sort_values(
            col_name,
            ascending=ascending,
            kind="mergesort",
        ).reset_index(drop=True)
        self._records = self._df.to_dict("records")
        self.layoutChanged.emit()

    def row_dict(self, row: int) -> dict:
        if row < 0 or row >= len(self._records):
            return {}
        return self._records[row]


class LiveTableView(QTableView):
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

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)

        for i, col in enumerate(LIVE_TABLE_COLUMNS):
            self.setColumnWidth(i, COLUMN_REGISTRY.get(col, {}).get("width", 90))

        self.clicked.connect(self._emit_row)
        self.doubleClicked.connect(self._copy_cell)

    def set_data(self, df: pd.DataFrame, highlight_wkns: set[str] | None = None) -> None:
        self.model_.set_frame(df, highlight_wkns)

    def _emit_row(self, index: QModelIndex) -> None:
        self.row_selected.emit(self.model_.row_dict(index.row()))

    def _copy_cell(self, index: QModelIndex) -> None:
        value = self.model_.display_value(index.row(), index.column())
        QApplication.clipboard().setText(value)
        QToolTip.showText(self.viewport().mapToGlobal(self.visualRect(index).center()), f"Copied: {value}")
