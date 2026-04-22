from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import QObject, QTimer

from app.core.state import Filters, LiveSessionState
from app.data.fake_feed import FakeFeed
from app.data.row_normalizer import normalize_rows
from app.engines.filter_engine import apply_live_filters
from app.engines.historical_engine import build_baseline_summary
from app.engines.live_engine import compute_kpis, merge_new_rows
from app.engines.pairtrade_adapter import compute_pair_summary
from app.ui.main_window import MainWindow
from app.utils.constants import DEFAULT_POLL_MS, START_HOUR


class AppController(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.window = MainWindow()
        self.feed = FakeFeed()
        self.state = LiveSessionState()

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(DEFAULT_POLL_MS)
        self.poll_timer.timeout.connect(self.poll_once)

        self._connect_ui()
        self._startup_load()
        self._sync_pending_from_active()
        self._refresh_ui()

        if self.window.tabs.currentIndex() == 0:
            self.start_polling()

    def _connect_ui(self) -> None:
        live = self.window.live_tab
        live.run_toggled.connect(self.set_running)
        live.poll_interval_changed.connect(self.set_poll_interval)
        live.filters_edited.connect(self._on_filters_edited)
        live.apply_filters_clicked.connect(self.apply_pending_filters)
        live.reset_filters_clicked.connect(self.reset_filters)
        self.window.live_tab_activated.connect(self._on_live_tab_activated)
        self.window.live_tab_deactivated.connect(self._on_live_tab_deactivated)

    def _startup_load(self) -> None:
        now = datetime.now().replace(microsecond=0)
        hist_start = now - timedelta(days=14)
        hist_end = now - timedelta(days=1)

        history_df = normalize_rows(self.feed.load_history(hist_start, hist_end))
        self.state.baseline_summary = build_baseline_summary(history_df, now)

        day_start = now.replace(hour=START_HOUR, minute=0, second=0, microsecond=0)
        today_df = normalize_rows(self.feed.load_today(day_start, now))
        self.state.raw_df = today_df
        self.state.last_refresh_at = now

    def _read_pending_filters_from_ui(self) -> Filters:
        fb = self.window.live_tab.filter_bar
        return Filters(
            action=tuple(fb.action_combo.checked_items()),
            category=tuple(fb.category_combo.checked_items()),
            side=tuple(fb.side_combo.checked_items()),
            wkn_text=fb.wkn_edit.text(),
            underlying_text=fb.underlying_edit.text(),
        )

    def _sync_pending_from_active(self) -> None:
        self.state.pending_filters = self.state.active_filters

    def show(self) -> None:
        self.window.show()

    def set_running(self, is_running: bool) -> None:
        self.state.is_running = is_running
        if is_running and self.window.tabs.currentIndex() == 0:
            self.start_polling()
        else:
            self.stop_polling()
        self._refresh_ui()

    def set_poll_interval(self, ms: int) -> None:
        self.poll_timer.setInterval(ms)

    def start_polling(self) -> None:
        if self.state.is_running and not self.poll_timer.isActive():
            self.poll_timer.start()

    def stop_polling(self) -> None:
        if self.poll_timer.isActive():
            self.poll_timer.stop()

    def _on_live_tab_activated(self) -> None:
        if self.state.is_running:
            self.poll_once()
            self.start_polling()
        self._refresh_ui()

    def _on_live_tab_deactivated(self) -> None:
        self.stop_polling()
        self._refresh_ui()

    def _on_filters_edited(self) -> None:
        self.state.pending_filters = self._read_pending_filters_from_ui()
        self._refresh_ui()

    def apply_pending_filters(self) -> None:
        if self.state.is_running:
            return
        self.state.active_filters = self._read_pending_filters_from_ui()
        self.state.pending_filters = self.state.active_filters
        self._refresh_ui()

    def reset_filters(self) -> None:
        if self.state.is_running:
            return
        fb = self.window.live_tab.filter_bar
        fb.action_combo.clear_checks()
        fb.category_combo.clear_checks()
        fb.side_combo.clear_checks()
        fb.wkn_edit.clear()
        fb.underlying_edit.clear()
        self.state.pending_filters = Filters()
        self.state.active_filters = Filters()
        self._refresh_ui()

    def poll_once(self) -> None:
        df_new, cursor = self.feed.poll_since(self.state.cursor)
        df_new = normalize_rows(df_new)
        self.state.raw_df = merge_new_rows(self.state.raw_df, df_new)
        self.state.cursor = cursor
        self.state.last_refresh_at = datetime.now().replace(microsecond=0)
        self._refresh_ui()

    def _pending_differs(self) -> bool:
        return self.state.pending_filters != self.state.active_filters

    def _refresh_ui(self) -> None:
        filtered_df = apply_live_filters(self.state.raw_df, self.state.active_filters)
        pair_summary = compute_pair_summary(filtered_df)
        kpis = compute_kpis(filtered_df, self.state.baseline_summary)

        live = self.window.live_tab
        live.kpi_rows.set_data(str(kpis["rows"]), f'vs hist {kpis["vs_rows"]:+.1f}%')
        live.kpi_trades.set_data(str(kpis["trades"]))
        live.kpi_quotes.set_data(str(kpis["quotes"]))
        live.kpi_qty.set_data(str(kpis["quantity"]), f'vs hist {kpis["vs_quantity"]:+.1f}%')
        live.kpi_pair_1.set_data(f'{pair_summary["pnl_1m"]:.2f}')
        live.kpi_pair_3.set_data(f'{pair_summary["pnl_3m"]:.2f}')

        latest = filtered_df.sort_values(["Time", "Id"], ascending=[False, False]).head(500).copy()
        live.live_table.set_data(latest, pair_summary["highlight_wkns"])

        ts = self.state.last_refresh_at.strftime("%Y-%m-%d %H:%M:%S") if self.state.last_refresh_at else "-"
        mode = "RUNNING" if self.state.is_running and self.window.tabs.currentIndex() == 0 else "PAUSED"
        live.set_last_update(f"Last update: {ts} | {mode}")

        live.set_filters_apply_enabled(not self.state.is_running)
        if self._pending_differs():
            if self.state.is_running:
                live.set_pending_text("Pending filters (apply when frozen)")
            else:
                live.set_pending_text("Pending filters ready")
        else:
            live.set_pending_text("")

        if latest.empty:
            live.detail_panel.set_row(None)
