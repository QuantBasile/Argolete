from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QFrame, QLabel, QTableView, QVBoxLayout


COLUMNS = ["Underlying", "TradedVolume", "Trades"]


class UnderlyingDashboardModel(QAbstractTableModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._records: list[dict] = []

    def set_frame(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        self._records = df.to_dict("records") if df is not None and not df.empty else []
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._records)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(COLUMNS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        rec = self._records[index.row()]
        col = COLUMNS[index.column()]
        value = rec.get(col, "")

        if role == Qt.DisplayRole:
            if col == "TradedVolume":
                try:
                    return f"{float(value):,.0f}"
                except Exception:
                    return str(value)
            if col == "Trades":
                try:
                    return f"{int(value):,}"
                except Exception:
                    return str(value)
            return str(value)

        if role == Qt.TextAlignmentRole and col in {"TradedVolume", "Trades"}:
            return Qt.AlignRight | Qt.AlignVCenter

        return None

    def headerData(self, section: int, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return {
                "Underlying": "Underlying",
                "TradedVolume": "Traded Volume",
                "Trades": "# Trades",
            }[COLUMNS[section]]
        return str(section + 1)


class UnderlyingDashboard(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("UnderlyingDashboard")

        self.title = QLabel("Top Underlyings — unfiltered")
        self.title.setObjectName("PanelTitle")

        self.table = QTableView()
        self.model_ = UnderlyingDashboardModel(self)
        self.table.setModel(self.model_)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.setMinimumHeight(230)
        self.table.setColumnWidth(0, 135)
        self.table.setColumnWidth(1, 125)
        self.table.setColumnWidth(2, 80)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.table, 1)

    def set_data(self, df: pd.DataFrame) -> None:
        self.model_.set_frame(df)
