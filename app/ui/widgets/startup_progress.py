from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


class StartupProgressWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Starting Turbo MM Live App")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.resize(460, 120)

        self.label = QLabel("Starting...")
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.bar)

    def update_progress(self, value: int, text: str) -> None:
        self.bar.setValue(value)
        self.label.setText(text)
