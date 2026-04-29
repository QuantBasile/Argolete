from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QTableView, QToolTip, QVBoxLayout


class DashboardTableModel(QAbstractTableModel):
    def __init__(self, columns: list[str], headers: dict[str, str] | None = None, parent=None) -> None:
        super().__init__(parent)
        self.columns = columns
        self.headers = headers or {c: c for c in columns}
        self._df = pd.DataFrame(columns=columns)
        self._records: list[dict] = []

    def set_frame(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        if df is None or df.empty:
            self._df = pd.DataFrame(columns=self.columns)
        else:
            self._df = df.loc[:, [c for c in self.columns if c in df.columns]].copy()
            for col in self.columns:
                if col not in self._df.columns:
                    self._df[col] = ""
            self._df = self._df[self.columns]
        self._records = self._df.to_dict("records") if not self._df.empty else []
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._records)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.columns)

    def display_value(self, row: int, column: int) -> str:
        if row < 0 or row >= len(self._records):
            return ""
        col = self.columns[column]
        value = self._records[row].get(col, "")
        if value is None or pd.isna(value):
            return ""
        if col in {"TradedVolume", "Volume", "TradeValue"}:
            try:
                return f"{float(value):,.0f}"
            except Exception:
                return str(value)
        if col in {"Trades", "Quotes", "Count"}:
            try:
                return f"{int(value):,}"
            except Exception:
                return str(value)
        if col in {"TradeQuoteRatio"}:
            try:
                return f"{float(value):.3f}"
            except Exception:
                return str(value)
        return str(value)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        col = self.columns[index.column()]

        if role == Qt.DisplayRole:
            return self.display_value(index.row(), index.column())

        if role == Qt.TextAlignmentRole and col in {"TradedVolume", "Trades", "Quotes", "Count", "TradeQuoteRatio"}:
            return Qt.AlignRight | Qt.AlignVCenter

        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.headers.get(self.columns[section], self.columns[section])
        return str(section + 1)

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        if self._df.empty:
            return

        col = self.columns[column]
        ascending = order == Qt.AscendingOrder

        self.layoutAboutToBeChanged.emit()
        self._df = self._df.sort_values(col, ascending=ascending, kind="mergesort").reset_index(drop=True)
        self._records = self._df.to_dict("records")
        self.layoutChanged.emit()


class DashboardTable(QFrame):
    def __init__(
        self,
        title: str,
        columns: list[str],
        headers: dict[str, str] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("DashboardTable")
        self.setMinimumHeight(235)

        self.title = QLabel(title)
        self.title.setObjectName("PanelTitle")

        self.table = QTableView()
        self.model_ = DashboardTableModel(columns=columns, headers=headers, parent=self)
        self.table.setModel(self.model_)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setMinimumHeight(165)
        self.table.doubleClicked.connect(self._copy_cell)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)
        layout.addWidget(self.title)
        layout.addWidget(self.table, 1)

    def set_data(self, df: pd.DataFrame) -> None:
        self.model_.set_frame(df)
        for i, col in enumerate(self.model_.columns):
            if col in {"Underlying", "Counterparty", "Reason", "Metric"}:
                self.table.setColumnWidth(i, 130)
            elif col == "Wkn":
                self.table.setColumnWidth(i, 85)
            elif col == "Time":
                self.table.setColumnWidth(i, 75)
            elif col == "TradedVolume":
                self.table.setColumnWidth(i, 115)
            else:
                self.table.setColumnWidth(i, 78)

    def _copy_cell(self, index: QModelIndex) -> None:
        value = self.model_.display_value(index.row(), index.column())
        QApplication.clipboard().setText(value)
        QToolTip.showText(self.table.viewport().mapToGlobal(self.table.visualRect(index).center()), f"Copied: {value}")
