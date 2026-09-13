"""Tests for the in-memory trade repository."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from analytics.models import Trade
from analytics.persistence.memory import InMemoryTradeRepository


def _make_trade(
    trade_id: str,
    *,
    symbol: str = "AAPL",
    timestamp: datetime | None = None,
    price: str = "100.00",
) -> Trade:
    """Create a valid trade fixture."""

    return Trade(
        event_id=f"event-{trade_id}",
        event_type="TRADE",
        trade_id=trade_id,
        symbol=symbol,
        price=Decimal(price),
        quantity=10,
        timestamp=timestamp or datetime(2026, 9, 13, 10, 0, 0),
        taker_side="BUY",
    )


def test_empty_repository_returns_none_and_empty_tuples() -> None:
    """An empty repository should return no stored trades."""

    repository = InMemoryTradeRepository()

    assert repository.get_by_id("missing") is None
    assert repository.list_by_symbol("AAPL") == ()
    assert repository.list_by_time_range(
        datetime(2026, 9, 13, 9, 0, 0),
        datetime(2026, 9, 13, 11, 0, 0),
    ) == ()


def test_save_and_get_by_id() -> None:
    """A saved trade should be retrievable by trade ID."""

    repository = InMemoryTradeRepository()
    trade = _make_trade("trade-001")

    repository.save(trade)

    assert repository.get_by_id("trade-001") is trade


def test_duplicate_trade_id_replaces_existing_trade() -> None:
    """Saving the same trade ID should replace the stored trade."""

    repository = InMemoryTradeRepository()

    original = _make_trade(
        "trade-001",
        price="100.00",
    )
    replacement = _make_trade(
        "trade-001",
        price="105.00",
    )

    repository.save(original)
    repository.save(replacement)

    assert repository.get_by_id("trade-001") is replacement
    assert repository.get_by_id("trade-001").price == Decimal("105.00")


def test_list_by_symbol_returns_matching_trades_in_insertion_order() -> None:
    """Symbol queries should preserve repository insertion order."""

    repository = InMemoryTradeRepository()

    trade_1 = _make_trade("trade-001", symbol="AAPL")
    trade_2 = _make_trade("trade-002", symbol="MSFT")
    trade_3 = _make_trade("trade-003", symbol="AAPL")

    repository.save(trade_1)
    repository.save(trade_2)
    repository.save(trade_3)

    assert repository.list_by_symbol("AAPL") == (
        trade_1,
        trade_3,
    )


def test_list_by_time_range_is_inclusive() -> None:
    """Time-range queries should include both boundary timestamps."""

    repository = InMemoryTradeRepository()

    start = datetime(2026, 9, 13, 10, 0, 0)
    middle = start + timedelta(minutes=5)
    end = start + timedelta(minutes=10)

    trade_before = _make_trade(
        "trade-before",
        timestamp=start - timedelta(seconds=1),
    )
    trade_start = _make_trade(
        "trade-start",
        timestamp=start,
    )
    trade_middle = _make_trade(
        "trade-middle",
        timestamp=middle,
    )
    trade_end = _make_trade(
        "trade-end",
        timestamp=end,
    )
    trade_after = _make_trade(
        "trade-after",
        timestamp=end + timedelta(seconds=1),
    )

    for trade in (
        trade_before,
        trade_start,
        trade_middle,
        trade_end,
        trade_after,
    ):
        repository.save(trade)

    assert repository.list_by_time_range(start, end) == (
        trade_start,
        trade_middle,
        trade_end,
    )


def test_list_by_time_range_rejects_reversed_range() -> None:
    """A reversed time range should raise ValueError."""

    repository = InMemoryTradeRepository()

    start = datetime(2026, 9, 13, 11, 0, 0)
    end = datetime(2026, 9, 13, 10, 0, 0)

    with pytest.raises(ValueError, match="start must not be after end"):
        repository.list_by_time_range(start, end)


def test_repository_instances_are_independent() -> None:
    """Separate repository instances should not share stored state."""

    first = InMemoryTradeRepository()
    second = InMemoryTradeRepository()

    trade = _make_trade("trade-001")

    first.save(trade)

    assert first.get_by_id("trade-001") is trade
    assert second.get_by_id("trade-001") is None


def test_save_rejects_non_trade_objects() -> None:
    """The repository should reject objects outside the Trade domain model."""

    repository = InMemoryTradeRepository()

    with pytest.raises(TypeError, match="trade must be a Trade"):
        repository.save("not-a-trade")  # type: ignore[arg-type]
