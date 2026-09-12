"""Trade domain model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class Trade:
    """An authoritative executed trade event from the engine."""

    event_id: str
    event_type: str
    trade_id: str
    symbol: str
    price: Decimal
    quantity: int
    timestamp: datetime
    taker_side: str
    buy_order_id: str | None = None
    sell_order_id: str | None = None
    taker_order_id: str | None = None
    maker_order_id: str | None = None

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("event_id must not be empty")

        if self.event_type != "TRADE":
            raise ValueError("event_type must be TRADE")

        if not self.trade_id:
            raise ValueError("trade_id must not be empty")

        if not self.symbol:
            raise ValueError("symbol must not be empty")

        if self.price <= 0:
            raise ValueError("price must be positive")

        if self.quantity <= 0:
            raise ValueError("quantity must be positive")

        if self.taker_side not in ("BUY", "SELL"):
            raise ValueError("taker_side must be BUY or SELL")

    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a JSON-friendly dictionary."""

        data = asdict(self)
        data["price"] = str(self.price)
        data["timestamp"] = self.timestamp.isoformat()
        return data
