from __future__ import annotations

COLUMN_REGISTRY = {
    "TimeDisplay": {"label": "Time", "width": 85, "format": "text"},
    "Wkn": {"label": "WKN", "width": 75, "format": "text"},
    "Underlying": {"label": "Underlying", "width": 110, "format": "text"},
    "Action": {"label": "Action", "width": 95, "format": "text"},
    "Side": {"label": "Side", "width": 70, "format": "text"},
    "TradePrice": {"label": "Price", "width": 90, "format": "price"},
    "Quantity": {"label": "Qty", "width": 90, "format": "int"},
    "TradeValue": {"label": "Notional", "width": 105, "format": "int"},
    "Category": {"label": "Category", "width": 100, "format": "text"},
    "Counterparty": {"label": "Counterparty", "width": 105, "format": "text"},
    "OptionType": {"label": "C/P", "width": 50, "format": "text"},
    "ContractSize": {"label": "C.Size", "width": 75, "format": "float"},
}

LIVE_TABLE_COLUMNS = [
    "TimeDisplay",
    "Wkn",
    "Underlying",
    "Action",
    "Side",
    "TradePrice",
    "Quantity",
    "TradeValue",
    "Category",
]

NUMERIC_COLUMNS = {"TradePrice", "Quantity", "TradeValue", "ContractSize"}
