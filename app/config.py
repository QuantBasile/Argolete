from __future__ import annotations

# Runtime data source.
# "fake" keeps current development mode.
# "sql" uses app.data.sql_feed.SqlFeed.
DATA_SOURCE = "fake"

# Polling / loading
POLL_INTERVAL_SECONDS = 10
START_HOUR = 2
HISTORY_DAYS = 14
SQL_PUFFER_SECONDS = 2
LIVE_TABLE_MAX_ROWS = 500

# Dashboard throttling
DASHBOARD_REFRESH_SECONDS = 30
DASHBOARD_REFRESH_EVERY_N_POLLS = 3

# Health / stale mode
STALE_WARNING_SECONDS = 30
STALE_PANIC_SECONDS = 90
SLOW_REFRESH_WARNING_MS = 250.0

# Trader defaults
MY_TRADER = "AUTO"

# Alert thresholds
HIGH_NOTIONAL_ALERT = 25_000.0

# SQL placeholder config.
# Fill in your own values or override via config_local.py.
SQL_DRIVER = ""
SQL_SERVER = ""
SQL_PORT = ""
SQL_DATABASE = ""
SQL_SCHEMA = ""
SQL_TABLE = ""

try:
    from app.config_local import *  # noqa: F401,F403
except Exception:
    pass
