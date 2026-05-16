from __future__ import annotations

from PySide6.QtWidgets import QLabel, QHBoxLayout, QWidget


class HealthBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.feed = QLabel("FEED: INIT")
        self.poll = QLabel("POLL: INIT")
        self.lag = QLabel("LAG: -")
        self.dashboard = QLabel("DASH: INIT")
        for lbl in [self.feed, self.poll, self.lag, self.dashboard]:
            lbl.setObjectName("HealthNeutral")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.feed)
        layout.addWidget(self.poll)
        layout.addWidget(self.lag)
        layout.addWidget(self.dashboard)

    def _set_chip(self, label: QLabel, text: str, status: str) -> None:
        label.setText(text)
        if status == "ok":
            obj = "HealthOk"
        elif status == "warn":
            obj = "HealthWarn"
        elif status == "panic":
            obj = "HealthPanic"
        else:
            obj = "HealthNeutral"
        label.setObjectName(obj)
        label.style().unpolish(label)
        label.style().polish(label)

    def set_health(self, feed: tuple[str, str], poll: tuple[str, str], lag: tuple[str, str], dashboard: tuple[str, str]) -> None:
        self._set_chip(self.feed, feed[0], feed[1])
        self._set_chip(self.poll, poll[0], poll[1])
        self._set_chip(self.lag, lag[0], lag[1])
        self._set_chip(self.dashboard, dashboard[0], dashboard[1])
