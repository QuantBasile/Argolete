"""Application-wide constants."""

from app import config

APP_TITLE = "Turbo MM Live App"

DEFAULT_POLL_MS = int(config.POLL_INTERVAL_SECONDS * 1000)
START_HOUR = config.START_HOUR
HISTORY_DAYS = config.HISTORY_DAYS
SQL_PUFFER_SECONDS = config.SQL_PUFFER_SECONDS

DASHBOARD_REFRESH_SECONDS = config.DASHBOARD_REFRESH_SECONDS
DASHBOARD_REFRESH_EVERY_N_POLLS = config.DASHBOARD_REFRESH_EVERY_N_POLLS
SLOW_REFRESH_WARNING_MS = config.SLOW_REFRESH_WARNING_MS
LIVE_TABLE_MAX_ROWS = config.LIVE_TABLE_MAX_ROWS
HIGH_NOTIONAL_ALERT = config.HIGH_NOTIONAL_ALERT
STALE_WARNING_SECONDS = config.STALE_WARNING_SECONDS
STALE_PANIC_SECONDS = config.STALE_PANIC_SECONDS
MY_TRADER = config.MY_TRADER

FINAL_SCHEMA_COLUMNS = [
    "Id", "OptionType", "Time", "Interface", "Wkn", "Underlying",
    "UnderlyingIsin", "UnderlyingNode", "Strike", "Expiry",
    "Action", "DetailedAction", "Counterparty", "Side", "TradePrice",
    "Quantity", "ContractSize", "Ref1", "Trader", "Agio",
    "Category", "EquityDeltaEq", "IsNextEventIn3Days",
]

DETAIL_COLUMN_ORDER = [
    *FINAL_SCHEMA_COLUMNS,
    "TradeValue",
    "Information",
    "HighlightReason",
]

PLACEHOLDER_TABS = [
    "Trade Log",
    "Pair Trades",
    "KO / Product Events",
    "Underlying Analysis",
    "Counterparty Analysis",
    "Debug / Profiling",
]
