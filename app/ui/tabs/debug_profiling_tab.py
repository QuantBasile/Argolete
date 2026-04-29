from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QGridLayout, QGroupBox, QVBoxLayout, QWidget


class DebugProfilingTab(QWidget):
    """Structured in-app debug/profiling console."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.runtime_labels = self._make_labels([
            "Mode", "Live tab active", "Poll interval", "Rows in memory", "Cursor time", "Dashboard refreshed",
        ])
        self.poll_labels = self._make_labels([
            "Status", "Last rows", "Poll ms", "Last event", "Lag seconds",
        ])
        self.refresh_labels = self._make_labels([
            "Reason", "Filter ms", "Metrics ms", "Dashboard ms", "Table ms", "Total ms", "Slow warning",
        ])
        self.sanity_labels = self._make_labels([
            "Duplicate IDs dropped", "Missing ID", "Missing Time", "Missing WKN", "Invalid TradeOK price", "Zero quantity",
        ])

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.clear_button = QPushButton("Clear debug log")
        self.clear_button.clicked.connect(self.text.clear)

        layout = QVBoxLayout(self)
        layout.addWidget(self._group("Runtime status", self.runtime_labels))
        layout.addWidget(self._group("Last poll quality", self.poll_labels))
        layout.addWidget(self._group("Last refresh timings", self.refresh_labels))
        layout.addWidget(self._group("Data sanity counters", self.sanity_labels))
        layout.addWidget(self.clear_button)
        layout.addWidget(self.text, 1)

    def _make_labels(self, keys: list[str]) -> dict[str, QLabel]:
        return {k: QLabel("-") for k in keys}

    def _group(self, title: str, labels: dict[str, QLabel]) -> QGroupBox:
        box = QGroupBox(title)
        grid = QGridLayout(box)
        for row, (key, label) in enumerate(labels.items()):
            grid.addWidget(QLabel(key), row, 0)
            grid.addWidget(label, row, 1)
        return box

    def add_message(self, message: str) -> None:
        self.text.append(message)

    def update_runtime(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            if key in self.runtime_labels:
                self.runtime_labels[key].setText(str(value))

    def update_poll(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            if key in self.poll_labels:
                self.poll_labels[key].setText(str(value))

    def update_refresh(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            if key in self.refresh_labels:
                self.refresh_labels[key].setText(str(value))

    def update_sanity(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            if key in self.sanity_labels:
                self.sanity_labels[key].setText(str(value))
