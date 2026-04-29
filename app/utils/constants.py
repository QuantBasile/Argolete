"""Application-wide constants."""

APP_TITLE = "Turbo MM Live App"
DEFAULT_POLL_MS = 10_000
START_HOUR = 2

# Right-side unfiltered dashboard is deliberately throttled.
DASHBOARD_REFRESH_SECONDS = 30
DASHBOARD_REFRESH_EVERY_N_POLLS = 3

# Performance guardrail.
SLOW_REFRESH_WARNING_MS = 250.0

# Latest rows displayed in live table.
LIVE_TABLE_MAX_ROWS = 500

# Priority alert thresholds for fake/demo data.
HIGH_NOTIONAL_ALERT = 25_000.0

DETAIL_COLUMN_ORDER = [
    "Id",
    "Time",
    "Wkn",
    "Underlying",
    "OptionType",
    "Action",
    "Counterparty",
    "Side",
    "TradePrice",
    "Quantity",
    "ContractSize",
    "Category",
    "TradeValue",
    "Information",
]

PLACEHOLDER_TABS = [
    "Trade Log",
    "Pair Trades",
    "KO / Product Events",
    "Underlying Analysis",
    "Counterparty Analysis",
    "Debug / Profiling",
]
