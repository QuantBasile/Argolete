from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class KpiCard(QFrame):
    """Compact KPI card."""

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.title_label = QLabel(title)
        self.value_label = QLabel("0")
        self.sub_label = QLabel("")

        self.title_label.setStyleSheet("font-weight: bold;")
        self.value_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.sub_label)

    def set_data(self, value: str, sub: str = "") -> None:
        self.value_label.setText(value)
        self.sub_label.setText(sub)
