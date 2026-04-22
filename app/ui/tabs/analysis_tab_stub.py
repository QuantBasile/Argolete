from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class AnalysisTabStub(QWidget):
    """Placeholder non-live tab."""

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"{title} — placeholder"))
        layout.addStretch(1)
