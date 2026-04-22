from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow, QTabWidget

from app.ui.tabs.analysis_tab_stub import AnalysisTabStub
from app.ui.tabs.live_overview_tab import LiveOverviewTab
from app.utils.constants import APP_TITLE, PLACEHOLDER_TABS


class MainWindow(QMainWindow):
    """Main application window."""

    live_tab_activated = Signal()
    live_tab_deactivated = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1500, 900)

        self.tabs = QTabWidget()
        self.live_tab = LiveOverviewTab()
        self.tabs.addTab(self.live_tab, "Live Overview")

        for title in PLACEHOLDER_TABS:
            self.tabs.addTab(AnalysisTabStub(title), title)

        self.setCentralWidget(self.tabs)
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index: int) -> None:
        if index == 0:
            self.live_tab_activated.emit()
        else:
            self.live_tab_deactivated.emit()
