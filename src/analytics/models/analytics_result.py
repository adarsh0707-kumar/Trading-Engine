"""Analytics result domain model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class AnalyticsResult:
    """Calculated analytics published downstream."""

    event_id: str
    event_type: str
    symbol: str
    price: Decimal
    vwap: Decimal | None
    sma: Decimal | None
    ema: Decimal | None
    position: int
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    equity: Decimal
    peak_equity: Decimal
    drawdown: Decimal
    timestamp: datetime

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("event_id must not be empty")

        if self.event_type != "ANALYTICS_UPDATE":
            raise ValueError("event_type must be ANALYTICS_UPDATE")

        if not self.symbol:
            raise ValueError("symbol must not be empty")

        if self.price <= 0:
            raise ValueError("price must be positive")

        if self.peak_equity < self.equity:
            raise ValueError("peak_equity must be greater than or equal to equity")

        if self.drawdown < 0:
            raise ValueError("drawdown must not be negative")

    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a JSON-friendly dictionary."""

        data = asdict(self)

        decimal_fields = (
            "price",
            "vwap",
            "sma",
            "ema",
            "realized_pnl",
            "unrealized_pnl",
            "equity",
            "peak_equity",
            "drawdown",
        )

        for field in decimal_fields:
            if data[field] is not None:
                data[field] = str(data[field])

        data["timestamp"] = self.timestamp.isoformat()
        return data
