from __future__ import annotations

COLUMN_REGISTRY = {
    "TimeDisplay": {"label": "Time", "width": 85, "format": "text"},
    "Id": {"label": "Id", "width": 105, "format": "text"},
    "OptionType": {"label": "C/P", "width": 50, "format": "text"},
    "Interface": {"label": "Interface", "width": 80, "format": "text"},
    "Wkn": {"label": "WKN", "width": 75, "format": "text"},
    "Underlying": {"label": "Underlying", "width": 110, "format": "text"},
    "UnderlyingIsin": {"label": "Und ISIN", "width": 115, "format": "text"},
    "UnderlyingNode": {"label": "Und Node", "width": 120, "format": "text"},
    "Strike": {"label": "Strike", "width": 75, "format": "float"},
    "Expiry": {"label": "Expiry", "width": 85, "format": "text"},
    "Action": {"label": "Action", "width": 105, "format": "text"},
    "DetailedAction": {"label": "Detailed", "width": 130, "format": "text"},
    "Counterparty": {"label": "Counterparty", "width": 105, "format": "text"},
    "Side": {"label": "Side", "width": 70, "format": "text"},
    "TradePrice": {"label": "Price", "width": 90, "format": "price"},
    "Quantity": {"label": "Qty", "width": 90, "format": "int"},
    "ContractSize": {"label": "C.Size", "width": 75, "format": "float"},
    "Ref1": {"label": "Ref1", "width": 85, "format": "price"},
    "Trader": {"label": "Trader", "width": 80, "format": "text"},
    "Agio": {"label": "Agio", "width": 80, "format": "float"},
    "Category": {"label": "Category", "width": 100, "format": "text"},
    "EquityDeltaEq": {"label": "DeltaEq", "width": 90, "format": "float"},
    "IsNextEventIn3Days": {"label": "Event<3d", "width": 75, "format": "bool"},
    "TradeValue": {"label": "Notional", "width": 105, "format": "int"},
}

LIVE_TABLE_COLUMNS = [
    "TimeDisplay", "Interface", "Wkn", "Underlying", "Action",
    "DetailedAction", "Side", "TradePrice", "Quantity", "TradeValue",
    "Ref1", "Trader", "Category",
]

NUMERIC_COLUMNS = {
    "TradePrice", "Quantity", "TradeValue", "ContractSize",
    "Strike", "Ref1", "Agio", "EquityDeltaEq",
}
