"""Market tick domain model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class Tick:
    """A market price/quantity observation."""

    event_id: str
    event_type: str
    symbol: str
    price: Decimal
    quantity: int
    timestamp: datetime

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("event_id must not be empty")

        if self.event_type != "MARKET_TICK":
            raise ValueError("event_type must be MARKET_TICK")

        if not self.symbol:
            raise ValueError("symbol must not be empty")

        if self.price <= 0:
            raise ValueError("price must be positive")

        if self.quantity <= 0:
            raise ValueError("quantity must be positive")

    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a JSON-friendly dictionary."""

        data = asdict(self)
        data["price"] = str(self.price)
        data["timestamp"] = self.timestamp.isoformat()
        return data
