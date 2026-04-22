"""Application-wide constants."""

APP_TITLE = "Turbo MM Live App"
DEFAULT_POLL_MS = 10_000
START_HOUR = 2

LIVE_VISIBLE_COLUMNS = [
    "Time",
    "Wkn",
    "Underlying",
    "Action",
    "Side",
    "TradePrice",
    "Quantity",
    "Category",
]

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
