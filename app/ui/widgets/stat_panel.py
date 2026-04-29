from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QGridLayout


class StatPanel(QFrame):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("StatPanel")
        self.title = QLabel(title)
        self.title.setObjectName("PanelTitle")
        self._labels: dict[str, QLabel] = {}

        self.layout_ = QGridLayout(self)
        self.layout_.setContentsMargins(10, 8, 10, 10)
        self.layout_.addWidget(self.title, 0, 0, 1, 2)

    def set_stats(self, stats: dict[str, str]) -> None:
        # Rebuild small panel; number of rows is tiny.
        while self.layout_.count() > 1:
            item = self.layout_.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        row = 1
        for key, value in stats.items():
            k = QLabel(key)
            v = QLabel(str(value))
            k.setObjectName("StatKey")
            v.setObjectName("StatValue")
            self.layout_.addWidget(k, row, 0)
            self.layout_.addWidget(v, row, 1)
            row += 1
