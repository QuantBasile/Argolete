from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMainWindow, QTabWidget

from app.ui.tabs.analysis_tab_stub import AnalysisTabStub
from app.ui.tabs.debug_profiling_tab import DebugProfilingTab
from app.ui.tabs.ko_argus_tab import KOArgusTab
from app.ui.tabs.live_overview_tab import LiveOverviewTab
from app.utils.constants import APP_TITLE, PLACEHOLDER_TABS


APP_STYLE = """
QMainWindow { background: #edf6ff; }

QTabWidget::pane {
    border: 1px solid #c7d7e8;
    border-radius: 12px;
    background: #f7fbff;
}

QTabBar::tab {
    background: #e7f2ff;
    border: 1px solid #c7d7e8;
    padding: 8px 14px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    color: #17324d;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: #ffffff;
    border-bottom-color: #ffffff;
    color: #005f9e;
}

QSplitter::handle { background: #d8e7f5; }
QScrollArea { border: 0px; background: transparent; }

QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #e5f6ff, stop:1 #ffffff);
    border: 1px solid #9fc7e8;
    border-radius: 10px;
    padding: 7px 12px;
    color: #12324c;
    font-weight: 700;
}

QPushButton:hover {
    border: 1px solid #4aa3df;
    background: #ffffff;
}

QLineEdit, QComboBox {
    background: #ffffff;
    border: 1px solid #bdd3ea;
    border-radius: 8px;
    padding: 5px 8px;
    color: #17324d;
}

#KpiCard {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffffff, stop:1 #eff8ff);
    border: 1px solid #cfe4f7;
    border-radius: 16px;
}

#KpiTitle {
    color: #58718a;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

#KpiValue {
    color: #102a43;
    font-size: 24px;
    font-weight: 900;
}

#KpiSub {
    color: #4e91c5;
    font-size: 11px;
    font-weight: 700;
}

QFrame {
    background: #ffffff;
    border: 1px solid #d8e7f5;
    border-radius: 14px;
}

QTableView {
    background: #ffffff;
    alternate-background-color: #f5faff;
    gridline-color: #e2edf7;
    border: 1px solid #d8e7f5;
    border-radius: 10px;
    selection-background-color: #b9e5ff;
    selection-color: #0f263d;
}

QHeaderView::section {
    background: #eaf5ff;
    color: #17324d;
    padding: 6px;
    border: 0px;
    border-right: 1px solid #d8e7f5;
    font-weight: 800;
}

#DashboardTable, #StatPanel {
    background: #ffffff;
    border: 1px solid #d8e7f5;
    border-radius: 16px;
}

#PanelTitle {
    color: #17324d;
    font-size: 13px;
    font-weight: 900;
    padding: 4px;
}

#SectionTitle {
    color: #0b3558;
    font-size: 15px;
    font-weight: 1000;
    padding: 4px;
}

#ModeLive {
    color: #075e38;
    background: #dff9ec;
    border: 1px solid #8ce0b8;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 900;
}

#ModeFrozen {
    color: #7a4b00;
    background: #fff2cc;
    border: 1px solid #e0bd62;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 900;
}

#HealthOk {
    color: #075e38;
    background: #dff9ec;
    border: 1px solid #8ce0b8;
    border-radius: 8px;
    padding: 4px 8px;
    font-weight: 900;
}

#HealthWarn {
    color: #7a4b00;
    background: #fff2cc;
    border: 1px solid #e0bd62;
    border-radius: 8px;
    padding: 4px 8px;
    font-weight: 900;
}

#HealthPanic {
    color: #8a1c1c;
    background: #ffe3e3;
    border: 1px solid #ff8787;
    border-radius: 8px;
    padding: 4px 8px;
    font-weight: 900;
}

#HealthNeutral {
    color: #364b63;
    background: #edf2f7;
    border: 1px solid #cbd5e0;
    border-radius: 8px;
    padding: 4px 8px;
    font-weight: 900;
}

#FilterSummary {
    color: #38536b;
    font-size: 11px;
    font-weight: 700;
    padding-left: 4px;
}

QTextEdit {
    background: #07111f;
    color: #d8f3ff;
    border-radius: 12px;
    font-family: monospace;
    font-size: 12px;
}
"""


class MainWindow(QMainWindow):
    live_tab_activated = Signal()
    live_tab_deactivated = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.setMinimumSize(1100, 700)
        self.resize(1800, 1000)
        self.setStyleSheet(APP_STYLE)

        self.tabs = QTabWidget()
        self.live_tab = LiveOverviewTab()
        self.debug_tab = DebugProfilingTab()
        self.ko_tab = KOArgusTab()

        self.tabs.addTab(self.live_tab, "Live Overview")

        for title in PLACEHOLDER_TABS:
            if title == "Debug / Profiling":
                self.tabs.addTab(self.debug_tab, title)
            elif title == "KO / Product Events":
                self.tabs.addTab(self.ko_tab, title)
            else:
                self.tabs.addTab(AnalysisTabStub(title), title)

        self.setCentralWidget(self.tabs)
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index: int) -> None:
        if index == 0:
            self.live_tab_activated.emit()
        else:
            self.live_tab_deactivated.emit()
