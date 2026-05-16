from __future__ import annotations

from datetime import datetime, timedelta
from time import perf_counter

import pandas as pd
from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication

from app import config
from app.core.state import Filters, LiveSessionState, PollQuality, RefreshProfile
from app.data.feed_factory import create_feed
from app.data.row_normalizer import normalize_rows
from app.data.schema_contract import build_column_availability, validate_schema
from app.engines.dashboard_engine import (
    build_agio_leaderboard,
    build_entity_trade_dashboard,
    build_error_strip,
    build_intraday_trade_curve,
    build_newly_active_wkns,
    build_next_event_monitor,
    build_pair_pnl_curve,
    build_priority_alerts,
    build_quote_dashboard,
    build_trade_quote_conversion,
    build_tradertimeout_by_category,
    build_tradertimeout_curve,
)
from app.engines.filter_engine import active_filter_summary, apply_live_filters
from app.engines.highlight_engine import apply_highlighting
from app.engines.historical_engine import build_baseline_summary, build_intraday_baseline_curve
from app.engines.live_engine import compute_kpis, compute_sanity_counters, merge_new_rows
from app.engines.pairtrade_adapter import compute_pair_summary
from app.ui.main_window import MainWindow
from app.ui.widgets.startup_progress import StartupProgressWindow
from app.utils.constants import (
    DASHBOARD_REFRESH_EVERY_N_POLLS, DASHBOARD_REFRESH_SECONDS, DEFAULT_POLL_MS,
    HISTORY_DAYS, LIVE_TABLE_MAX_ROWS, MY_TRADER, SLOW_REFRESH_WARNING_MS,
    SQL_PUFFER_SECONDS, STALE_PANIC_SECONDS, STALE_WARNING_SECONDS, START_HOUR,
)


class AppController(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.progress = StartupProgressWindow()
        self.progress.show()
        QApplication.processEvents()

        self.window = MainWindow()
        self.feed = create_feed()
        self.state = LiveSessionState()
        self.poll_interval_ms = DEFAULT_POLL_MS

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(DEFAULT_POLL_MS)
        self.poll_timer.timeout.connect(self.poll_once)

        self._progress(10, "Connecting UI...")
        self._connect_ui()
        self._log("APP START")
        self._log(f"DATA_SOURCE={config.DATA_SOURCE}")
        self._startup_load()
        self._sync_pending_from_active()
        self._refresh_ui(reason="startup", force_dashboard=True)

        if self.window.tabs.currentIndex() == 0:
            self.start_polling()

        self._progress(100, "Ready")
        self.progress.close()

    def _progress(self, value: int, text: str) -> None:
        if hasattr(self, "progress") and self.progress:
            self.progress.update_progress(value, text)
            QApplication.processEvents()

    def _log(self, message: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {message}"
        print(line)
        if hasattr(self, "window") and hasattr(self.window, "debug_tab"):
            self.window.debug_tab.add_message(line)

    def _connect_ui(self) -> None:
        live = self.window.live_tab
        live.run_toggled.connect(self.set_running)
        live.poll_interval_changed.connect(self.set_poll_interval)
        live.filters_edited.connect(self._on_filters_edited)
        live.apply_filters_clicked.connect(self.apply_pending_filters)
        live.reset_filters_clicked.connect(self.reset_filters)
        live.filter_preset_selected.connect(self.apply_filter_preset)
        self.window.live_tab_activated.connect(self._on_live_tab_activated)
        self.window.live_tab_deactivated.connect(self._on_live_tab_deactivated)

    def _schema_check(self, raw_df: pd.DataFrame, label: str) -> None:
        report = validate_schema(raw_df)
        self.state.schema_report = report
        self.state.column_availability = build_column_availability(raw_df)

        for warning in report.get("warnings", []):
            self._log(f"SCHEMA {label}: {warning}")

    def _startup_load(self) -> None:
        t0 = perf_counter()
        now = datetime.now().replace(microsecond=0)

        self._progress(25, "Loading historical data...")
        hist_start = now - timedelta(days=HISTORY_DAYS)
        hist_end = now - timedelta(days=1)

        raw_history = self.feed.load_history(hist_start, hist_end)
        self._schema_check(raw_history, "history")
        history_df = normalize_rows(raw_history)
        self.state.baseline_summary = build_baseline_summary(history_df, now)
        self.state.baseline_curve = build_intraday_baseline_curve(history_df)
        t_hist = perf_counter()

        self._progress(55, "Loading today's data...")
        day_start = now.replace(hour=START_HOUR, minute=0, second=0, microsecond=0)
        raw_today = self.feed.load_today(day_start, now)
        self.state.last_raw_poll_df = raw_today.tail(20).copy()
        self._schema_check(raw_today, "today")
        today_df = normalize_rows(raw_today)

        self._progress(75, "Normalizing and building baselines...")
        self.state.raw_df = today_df
        self.state.live_df = today_df.copy()
        self.state.last_refresh_at = now
        self.state.sanity = compute_sanity_counters(self.state.live_df)
        self._update_poll_quality(last_rows=len(today_df), poll_ms=0.0, status="STARTUP")
        self.state.cursor.last_successful_poll_time = now
        self.state.cursor.last_event_time = self.state.poll_quality.last_event_time
        self.state.cursor.status = "STARTUP"
        t_today = perf_counter()

        self._log(f"Historical data loaded: rows={len(history_df):,}, baseline_buckets={len(self.state.baseline_curve):,}, time={(t_hist - t0) * 1000:.1f}ms")
        self._log(f"Today data loaded: rows={len(today_df):,}, time={(t_today - t_hist) * 1000:.1f}ms")

    def _read_pending_filters_from_ui(self) -> Filters:
        fb = self.window.live_tab.filter_bar
        return Filters(
            action=tuple(fb.action_combo.checked_items()),
            category=tuple(fb.category_combo.checked_items()),
            side=tuple(fb.side_combo.checked_items()),
            trader=tuple(fb.trader_combo.checked_items()),
            interface=tuple(fb.interface_combo.checked_items()),
            wkn_text=fb.wkn_edit.text(),
            underlying_text=fb.underlying_edit.text(),
            pairs_only_table=fb.pairs_only.isChecked(),
            next_event_only=fb.next_event_only.isChecked(),
        )

    def _sync_pending_from_active(self) -> None:
        self.state.pending_filters = self.state.active_filters

    def show(self) -> None:
        self.window.show()

    def set_running(self, is_running: bool) -> None:
        self.state.is_running = is_running
        if is_running and self.window.tabs.currentIndex() == 0:
            self.start_polling()
            self._log("Polling resumed: RUNNING LIVE")
        else:
            self.stop_polling()
            self._log("Polling frozen: SNAPSHOT MODE")
        self._refresh_ui(reason="run-toggle")

    def set_poll_interval(self, ms: int) -> None:
        self.poll_interval_ms = ms
        self.poll_timer.setInterval(ms)
        self._log(f"Polling interval changed to {ms / 1000:.0f}s")
        self._update_debug_panels()

    def start_polling(self) -> None:
        if self.state.is_running and not self.poll_timer.isActive():
            self.poll_timer.start()
            self._log("Polling timer started")

    def stop_polling(self) -> None:
        if self.poll_timer.isActive():
            self.poll_timer.stop()
            self._log("Polling timer stopped")

    def _on_live_tab_activated(self) -> None:
        if self.state.is_running:
            self._log("Live tab activated: catch-up poll")
            self.poll_once()
            self.start_polling()
        self._refresh_ui(reason="tab-activated")

    def _on_live_tab_deactivated(self) -> None:
        self._log("Live tab deactivated: pausing polling")
        self.stop_polling()
        self._refresh_ui(reason="tab-deactivated")

    def _on_filters_edited(self) -> None:
        self.state.pending_filters = self._read_pending_filters_from_ui()
        self.state.active_filters = self.state.pending_filters
        self._refresh_ui(reason="filters-edited")

    def apply_pending_filters(self) -> None:
        self.state.active_filters = self._read_pending_filters_from_ui()
        self.state.pending_filters = self.state.active_filters
        self._refresh_ui(reason="apply-filters")

    def reset_filters(self) -> None:
        fb = self.window.live_tab.filter_bar
        fb.clear_all()
        self.state.pending_filters = Filters()
        self.state.active_filters = Filters()
        self._refresh_ui(reason="reset-filters")

    def apply_filter_preset(self, preset: str) -> None:
        fb = self.window.live_tab.filter_bar
        fb.clear_all()

        if preset == "TradeOK":
            fb.action_combo.set_checked_items(["TradeOK"])
        elif preset == "Errors":
            fb.action_combo.set_checked_items(["QuoteError", "TradeError"])
        elif preset == "TraderTimeout":
            fb.action_combo.set_checked_items(["QuoteError", "TradeError", "QuoteOK", "TradeOK"])
        elif preset == "SoldOut":
            fb.action_combo.set_checked_items(["QuoteError", "TradeError", "Info"])
        elif preset == "NextEvent<3d":
            fb.next_event_only.setChecked(True)
        elif preset == "MyTrader":
            fb.trader_combo.set_checked_items([MY_TRADER])

        self.state.active_filters = self._read_pending_filters_from_ui()
        self.state.pending_filters = self.state.active_filters
        self._refresh_ui(reason=f"preset-{preset}")

    def poll_once(self) -> None:
        t0 = perf_counter()
        try:
            query_from = self.state.cursor.last_event_time - timedelta(seconds=SQL_PUFFER_SECONDS) if self.state.cursor.last_event_time else None
            query_to = datetime.now()
            self.state.cursor.last_sql_query_from = query_from
            self.state.cursor.last_sql_query_to = query_to

            raw_new, cursor = self.feed.poll_since(self.state.cursor)
            self.state.last_raw_poll_df = raw_new.tail(20).copy()
            self._schema_check(raw_new, "poll")
            df_new = normalize_rows(raw_new)
            merged, dropped = merge_new_rows(self.state.raw_df, df_new)

            self.state.raw_df = merged
            self.state.live_df = merged.copy()
            self.state.cursor = cursor
            self.state.cursor.last_sql_query_from = query_from
            self.state.cursor.last_sql_query_to = query_to
            self.state.cursor.last_successful_poll_time = datetime.now()
            self.state.last_refresh_at = datetime.now().replace(microsecond=0)
            self.state.sanity = compute_sanity_counters(self.state.live_df, duplicate_ids_dropped=dropped)

            t1 = perf_counter()
            self._update_poll_quality(last_rows=len(df_new), poll_ms=(t1 - t0) * 1000.0, status="OK")
            self.state.cursor.last_event_time = self.state.poll_quality.last_event_time
            self.state.cursor.status = "OK"
            self.state.dashboard_poll_counter += 1
            self._log(f"Poll success: new_rows={len(df_new):,}, duplicate_ids_dropped={dropped:,}, total_rows={len(self.state.live_df):,}, time={(t1 - t0) * 1000:.1f}ms")
        except Exception as exc:
            t1 = perf_counter()
            self._update_poll_quality(last_rows=0, poll_ms=(t1 - t0) * 1000.0, status=f"ERROR: {exc}")
            self.state.cursor.status = f"ERROR: {exc}"
            self._log(f"Poll ERROR: {exc}")
            return
        self._refresh_ui(reason="poll")

    def _update_poll_quality(self, last_rows: int, poll_ms: float, status: str) -> None:
        last_event = None
        lag_seconds = 0.0
        if self.state.live_df is not None and not self.state.live_df.empty:
            last_event = pd.to_datetime(self.state.live_df["Time"], errors="coerce").max()
            if pd.notna(last_event):
                last_event_dt = last_event.to_pydatetime() if hasattr(last_event, "to_pydatetime") else last_event
                lag_seconds = max((datetime.now() - last_event_dt).total_seconds(), 0.0)
                last_event = last_event_dt
        self.state.poll_quality = PollQuality(last_rows=last_rows, last_poll_ms=poll_ms, total_rows=len(self.state.live_df) if self.state.live_df is not None else 0, last_event_time=last_event, lag_seconds=lag_seconds, status=status)

    def _should_refresh_dashboard(self, force: bool = False) -> bool:
        if force or not self.state.dashboard_cache or self.state.dashboard_last_refresh_at is None:
            return True
        now = datetime.now()
        if (now - self.state.dashboard_last_refresh_at).total_seconds() >= DASHBOARD_REFRESH_SECONDS:
            return True
        return self.state.dashboard_poll_counter >= DASHBOARD_REFRESH_EVERY_N_POLLS

    def _build_dashboard_cache(self, pair_summary: dict, force: bool = False) -> tuple[dict, float]:
        if not self._should_refresh_dashboard(force=force):
            return self.state.dashboard_cache, 0.0

        t0 = perf_counter()
        now = datetime.now()
        try:
            agio = build_agio_leaderboard(self.state.live_df, top_n=10)
            agio_top = agio.loc[agio["Bucket"].eq("Top 10")].copy().sort_values("CumAgio", ascending=False)
            agio_floor = agio.loc[agio["Bucket"].eq("Floor 10")].copy().sort_values("CumAgio", ascending=True)

            cache = {
                "curve": build_intraday_trade_curve(self.state.live_df, baseline_curve=self.state.baseline_curve),
                "underlying": build_entity_trade_dashboard(self.state.live_df, key="Underlying", top_n=10),
                "wkn": build_entity_trade_dashboard(self.state.live_df, key="Wkn", top_n=10),
                "counterparty": build_entity_trade_dashboard(self.state.live_df, key="Counterparty", top_n=10),
                "quoted_wkn": build_quote_dashboard(self.state.live_df, key="Wkn", top_n=10),
                "new_wkn": build_newly_active_wkns(self.state.live_df, now=now, minutes=5, top_n=10),
                "conversion": build_trade_quote_conversion(self.state.live_df, key="Underlying", top_n=10),
                "errors": build_error_strip(self.state.live_df, now=now, minutes=5),
                "priority": build_priority_alerts(self.state.live_df, pair_summary.get("highlight_wkns", set()), now=now, top_n=12),
                "timeout_curve": build_tradertimeout_curve(self.state.live_df),
                "timeout_category": build_tradertimeout_by_category(self.state.live_df, top_n=12),
                "next_event": build_next_event_monitor(self.state.live_df, top_n=10),
                "agio_top": agio_top,
                "agio_floor": agio_floor,
            }
            self.state.dashboard_cache = cache
            self.state.dashboard_last_refresh_at = now
            self.state.dashboard_poll_counter = 0
            self.state.dashboard_status = "OK"
        except Exception as exc:
            self.state.dashboard_status = f"ERROR: {exc}"
            self._log(f"Dashboard ERROR, keeping previous cache: {exc}")
        return self.state.dashboard_cache, (perf_counter() - t0) * 1000.0

    def _refresh_status_only(self) -> None:
        live = self.window.live_tab
        live.set_filters_apply_enabled(True)
        live.set_pending_text("")
        live.set_mode(self.state.is_running and self.window.tabs.currentIndex() == 0)

    def _fmt_pct(self, value: float) -> str:
        return f"vs hist {value:+.1f}%"

    def _fmt_num(self, value: float) -> str:
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if abs(value) >= 1_000:
            return f"{value / 1_000:.1f}k"
        return f"{value:,.0f}"

    def _health_status(self):
        pq = self.state.poll_quality
        if pq.status.startswith("ERROR"):
            poll = ("POLL: ERROR", "panic")
        else:
            poll = ("POLL: OK", "ok")

        feed = (f"FEED: {config.DATA_SOURCE.upper()}", "ok" if not pq.status.startswith("ERROR") else "panic")

        lag = pq.lag_seconds
        if lag >= STALE_PANIC_SECONDS:
            lag_chip = (f"PANIC STALE: {lag:.0f}s", "panic")
        elif lag >= STALE_WARNING_SECONDS:
            lag_chip = (f"LAG: {lag:.0f}s", "warn")
        else:
            lag_chip = (f"LAG: {lag:.0f}s", "ok")

        dash = ("DASH: OK", "ok") if self.state.dashboard_status == "OK" else ("DASH: WARN", "warn")
        return feed, poll, lag_chip, dash

    def _refresh_ui(self, reason: str = "refresh", force_dashboard: bool = False) -> None:
        t0 = perf_counter()
        filtered_df = apply_live_filters(self.state.live_df, self.state.active_filters)
        t_filter = perf_counter()

        pair_summary = compute_pair_summary(filtered_df)
        highlighted_filtered = apply_highlighting(filtered_df, pair_summary["highlight_wkns"])
        pair_curve = build_pair_pnl_curve(highlighted_filtered, pair_summary["highlight_wkns"])
        filtered_flow_curve = build_intraday_trade_curve(highlighted_filtered, baseline_curve=None)
        kpis = compute_kpis(highlighted_filtered, self.state.baseline_summary, total_rows=len(self.state.live_df))
        t_metrics = perf_counter()

        dashboard_cache, dashboard_ms = self._build_dashboard_cache(pair_summary, force=force_dashboard)
        t_dashboard = perf_counter()

        live = self.window.live_tab
        live.kpi_rows.set_data(f'{kpis["rows"]:,} / {kpis["total_rows"]:,}', "filtered / raw")
        live.kpi_trades.set_data(f'{kpis["trades"]:,}', self._fmt_pct(kpis["vs_trades"]))
        live.kpi_quotes.set_data(f'{kpis["quotes"]:,}', self._fmt_pct(kpis["vs_quotes"]))
        live.kpi_qty.set_data(f'{kpis["quantity"]:,}', self._fmt_pct(kpis["vs_quantity"]))
        live.kpi_traded_volume.set_data(self._fmt_num(kpis["trade_volume"]), self._fmt_pct(kpis["vs_trade_volume"]))
        live.kpi_buy_sell_ratio.set_data(f'{kpis["buy_sell_ratio"]:.2f}', self._fmt_pct(kpis["vs_buy_sell_ratio"]))
        live.kpi_trade_quote_ratio.set_data(f'{kpis["trade_quote_ratio"]:.3f}', self._fmt_pct(kpis["vs_trade_quote_ratio"]))
        live.kpi_pair_1.set_data(f'{pair_summary["pnl_1m"]:.2f}', "dummy module")

        live.pair_pnl_curve.set_data(pair_curve)
        live.filtered_flow_curve.set_data(filtered_flow_curve)
        live.flow_curve.set_data(dashboard_cache.get("curve"))
        live.tbl_underlying.set_data(dashboard_cache.get("underlying"))
        live.tbl_wkn.set_data(dashboard_cache.get("wkn"))
        live.tbl_counterparty.set_data(dashboard_cache.get("counterparty"))
        live.tbl_new_wkn.set_data(dashboard_cache.get("new_wkn"))
        live.tbl_conversion.set_data(dashboard_cache.get("conversion"))
        live.tbl_errors.set_data(dashboard_cache.get("errors"))
        live.tbl_priority.set_data(dashboard_cache.get("priority"))
        live.timeout_curve.set_data(dashboard_cache.get("timeout_curve"))
        live.chart_timeout_category.set_data(dashboard_cache.get("timeout_category"))
        live.tbl_next_event.set_data(dashboard_cache.get("next_event"))
        live.chart_quoted_wkn.set_data(dashboard_cache.get("quoted_wkn"))
        live.chart_agio_top.set_data(dashboard_cache.get("agio_top"))
        live.chart_agio_floor.set_data(dashboard_cache.get("agio_floor"))

        table_df = highlighted_filtered
        if self.state.active_filters.pairs_only_table:
            table_df = highlighted_filtered.loc[highlighted_filtered["Wkn"].isin(pair_summary["highlight_wkns"])]

        latest = table_df.head(LIVE_TABLE_MAX_ROWS).copy()
        self.state.display_df = latest
        live.live_table.set_data(latest, pair_summary["highlight_wkns"])
        t_table = perf_counter()

        ts = self.state.last_refresh_at.strftime("%Y-%m-%d %H:%M:%S") if self.state.last_refresh_at else "-"
        mode = "RUNNING" if self.state.is_running and self.window.tabs.currentIndex() == 0 else "PAUSED"
        live.set_last_update(f"Last update: {ts} | {mode}")
        live.set_filter_summary(active_filter_summary(self.state.active_filters, len(self.state.live_df), len(highlighted_filtered)))
        live.health_bar.set_health(*self._health_status())

        self._refresh_status_only()
        if latest.empty:
            live.detail_panel.set_row(None)

        t_end = perf_counter()
        total_ms = (t_end - t0) * 1000.0
        slow = total_ms > SLOW_REFRESH_WARNING_MS
        self.state.refresh_profile = RefreshProfile(
            reason=reason,
            filter_ms=(t_filter - t0) * 1000.0,
            metrics_ms=(t_metrics - t_filter) * 1000.0,
            dashboard_ms=dashboard_ms,
            table_ms=(t_table - t_dashboard) * 1000.0,
            total_ms=total_ms,
            slow_warning=slow,
        )

        msg = (
            f"[refresh:{reason}] rows={len(self.state.live_df):,} filtered={len(highlighted_filtered):,} "
            f"table_rows={len(latest):,} filter={self.state.refresh_profile.filter_ms:.1f}ms "
            f"metrics={self.state.refresh_profile.metrics_ms:.1f}ms "
            f"dashboard={self.state.refresh_profile.dashboard_ms:.1f}ms "
            f"table={self.state.refresh_profile.table_ms:.1f}ms total={self.state.refresh_profile.total_ms:.1f}ms"
        )
        self._log(msg)
        if slow:
            self._log(f"WARNING slow refresh: {total_ms:.1f}ms reason={reason}")
        self._update_debug_panels()

    def _update_debug_panels(self) -> None:
        if not hasattr(self.window, "debug_tab"):
            return
        pq = self.state.poll_quality
        rp = self.state.refresh_profile
        sanity = self.state.sanity
        schema_warnings = len(self.state.schema_report.get("warnings", [])) if self.state.schema_report else 0
        self.window.debug_tab.update_runtime({
            "Mode": "RUNNING LIVE" if self.state.is_running and self.window.tabs.currentIndex() == 0 else "SNAPSHOT / PAUSED",
            "Live tab active": str(self.window.tabs.currentIndex() == 0),
            "Poll interval": f"{self.poll_interval_ms / 1000:.0f}s",
            "Rows in memory": f"{len(self.state.live_df):,}",
            "Cursor time": self.state.cursor.last_time.strftime("%H:%M:%S") if self.state.cursor.last_time else "-",
            "Dashboard refreshed": self.state.dashboard_last_refresh_at.strftime("%H:%M:%S") if self.state.dashboard_last_refresh_at else "-",
            "Schema drift": f"{schema_warnings} warnings",
        })
        self.window.debug_tab.update_poll({
            "Status": pq.status,
            "Last rows": f"{pq.last_rows:,}",
            "Poll ms": f"{pq.last_poll_ms:.1f}",
            "Last event": pq.last_event_time.strftime("%Y-%m-%d %H:%M:%S") if pq.last_event_time else "-",
            "Lag seconds": f"{pq.lag_seconds:.1f}",
            "Query from": self.state.cursor.last_sql_query_from.strftime("%Y-%m-%d %H:%M:%S") if self.state.cursor.last_sql_query_from else "-",
            "Query to": self.state.cursor.last_sql_query_to.strftime("%Y-%m-%d %H:%M:%S") if self.state.cursor.last_sql_query_to else "-",
        })
        self.window.debug_tab.update_refresh({
            "Reason": rp.reason,
            "Filter ms": f"{rp.filter_ms:.1f}",
            "Metrics ms": f"{rp.metrics_ms:.1f}",
            "Dashboard ms": f"{rp.dashboard_ms:.1f}",
            "Table ms": f"{rp.table_ms:.1f}",
            "Total ms": f"{rp.total_ms:.1f}",
            "Slow warning": str(rp.slow_warning),
        })
        self.window.debug_tab.update_sanity({
            "Duplicate IDs dropped": f"{sanity.duplicate_ids_dropped:,}",
            "Missing ID": f"{sanity.missing_id:,}",
            "Missing Time": f"{sanity.missing_time:,}",
            "Missing WKN": f"{sanity.missing_wkn:,}",
            "Invalid TradeOK price": f"{sanity.invalid_trade_price:,}",
            "Zero quantity": f"{sanity.zero_quantity:,}",
        })

        raw = self.state.last_raw_poll_df.copy()
        if raw is not None and not raw.empty:
            if "Time" in raw.columns:
                raw["Time"] = pd.to_datetime(raw["Time"], errors="coerce").dt.strftime("%H:%M:%S")
            self.window.debug_tab.raw_rows_table.set_data(raw.tail(10))
        self.window.debug_tab.column_table.set_data(self.state.column_availability)
