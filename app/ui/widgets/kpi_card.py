from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class KpiCard(QFrame):
    """Readable compact KPI card.

    Intentionally simple: labels only, no heavy rendering.
    """

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("KpiCard")
        self.setMinimumHeight(82)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("KpiTitle")

        self.value_label = QLabel("0")
        self.value_label.setObjectName("KpiValue")
        self.value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.sub_label = QLabel("")
        self.sub_label.setObjectName("KpiSub")
        self.sub_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.sub_label)

    def set_data(self, value: str, sub: str = "") -> None:
        self.value_label.setText(value)
        self.sub_label.setText(sub)
