"""Unit tests for risk-event generation."""

from datetime import datetime
from decimal import Decimal

import pytest

from analytics.models.risk_event import RiskEvent, RiskEventType
from analytics.models.risk_limit import (
    RiskLimit,
    RiskLimitState,
    RiskLimitStatus,
    RiskLimitType,
)
from analytics.risk.event_generator import RiskEventGenerator


TIMESTAMP = datetime(2026, 9, 13, 12, 0, 0)


def make_state(
    *,
    status: RiskLimitStatus,
    current_value: str = "80",
) -> RiskLimitState:
    """Create a representative risk-limit state."""

    limit = RiskLimit(
        limit_type=RiskLimitType.MAX_POSITION,
        threshold=Decimal("100"),
        warning_threshold=Decimal("80"),
        symbol="BTC",
    )

    return RiskLimitState(
        limit=limit,
        current_value=Decimal(current_value),
        status=status,
    )


def test_warning_state_generates_warning_event() -> None:
    generator = RiskEventGenerator()

    events = generator.generate(
        states=(make_state(status=RiskLimitStatus.WARNING),),
        timestamp=TIMESTAMP,
    )

    assert len(events) == 1

    event = events[0]

    assert event.event_type == RiskEventType.LIMIT_WARNING
    assert event.status == RiskLimitStatus.WARNING
    assert event.symbol == "BTC"
    assert event.limit_type == RiskLimitType.MAX_POSITION
    assert event.current_value == Decimal("80")


def test_breached_state_generates_breached_event() -> None:
    generator = RiskEventGenerator()

    events = generator.generate(
        states=(
            make_state(
                status=RiskLimitStatus.BREACHED,
                current_value="100",
            ),
        ),
        timestamp=TIMESTAMP,
    )

    assert len(events) == 1

    event = events[0]

    assert event.event_type == RiskEventType.LIMIT_BREACHED
    assert event.status == RiskLimitStatus.BREACHED
    assert event.current_value == Decimal("100")


def test_ok_state_does_not_generate_event() -> None:
    generator = RiskEventGenerator()

    events = generator.generate(
        states=(make_state(status=RiskLimitStatus.OK, current_value="50"),),
        timestamp=TIMESTAMP,
    )

    assert events == ()


def test_multiple_states_generate_only_actionable_events() -> None:
    generator = RiskEventGenerator()

    states = (
        make_state(
            status=RiskLimitStatus.OK,
            current_value="50",
        ),
        make_state(
            status=RiskLimitStatus.WARNING,
            current_value="80",
        ),
        make_state(
            status=RiskLimitStatus.BREACHED,
            current_value="100",
        ),
    )

    events = generator.generate(
        states=states,
        timestamp=TIMESTAMP,
    )

    assert len(events) == 2
    assert events[0].status == RiskLimitStatus.WARNING
    assert events[1].status == RiskLimitStatus.BREACHED


def test_event_ids_are_sequential() -> None:
    generator = RiskEventGenerator()

    states = (
        make_state(status=RiskLimitStatus.WARNING),
        make_state(status=RiskLimitStatus.BREACHED, current_value="100"),
    )

    events = generator.generate(
        states=states,
        timestamp=TIMESTAMP,
    )

    assert events[0].event_id == "risk-max_position-1"
    assert events[1].event_id == "risk-max_position-2"


def test_custom_event_prefix_is_used() -> None:
    generator = RiskEventGenerator(event_prefix="analytics")

    events = generator.generate(
        states=(make_state(status=RiskLimitStatus.WARNING),),
        timestamp=TIMESTAMP,
    )

    assert events[0].event_id == "analytics-max_position-1"


def test_event_serializes_to_dict() -> None:
    state = make_state(
        status=RiskLimitStatus.BREACHED,
        current_value="125",
    )

    event = RiskEvent.from_state(
        event_id="risk-max_position-1",
        state=state,
        timestamp=TIMESTAMP,
    )

    data = event.to_dict()

    assert data == {
        "event_id": "risk-max_position-1",
        "event_type": "RISK_LIMIT_BREACHED",
        "symbol": "BTC",
        "limit_type": "max_position",
        "status": "breached",
        "threshold": "100",
        "warning_threshold": "80",
        "current_value": "125",
        "timestamp": "2026-09-13T12:00:00",
    }


def test_ok_state_cannot_be_converted_to_event() -> None:
    state = make_state(
        status=RiskLimitStatus.OK,
        current_value="50",
    )

    with pytest.raises(
        ValueError,
        match="only be created for WARNING or BREACHED",
    ):
        RiskEvent.from_state(
            event_id="risk-max_position-1",
            state=state,
            timestamp=TIMESTAMP,
        )


def test_warning_event_requires_warning_status() -> None:
    with pytest.raises(
        ValueError,
        match="LIMIT_WARNING events must have WARNING status",
    ):
        RiskEvent(
            event_id="risk-1",
            event_type=RiskEventType.LIMIT_WARNING,
            symbol="BTC",
            limit_type=RiskLimitType.MAX_POSITION,
            status=RiskLimitStatus.BREACHED,
            threshold=Decimal("100"),
            warning_threshold=Decimal("80"),
            current_value=Decimal("90"),
            timestamp=TIMESTAMP,
        )


def test_breached_event_requires_breached_status() -> None:
    with pytest.raises(
        ValueError,
        match="LIMIT_BREACHED events must have BREACHED status",
    ):
        RiskEvent(
            event_id="risk-1",
            event_type=RiskEventType.LIMIT_BREACHED,
            symbol="BTC",
            limit_type=RiskLimitType.MAX_POSITION,
            status=RiskLimitStatus.WARNING,
            threshold=Decimal("100"),
            warning_threshold=Decimal("80"),
            current_value=Decimal("90"),
            timestamp=TIMESTAMP,
        )


def test_generator_rejects_blank_prefix() -> None:
    with pytest.raises(
        ValueError,
        match="event_prefix must not be blank",
    ):
        RiskEventGenerator(event_prefix="   ")


def test_event_rejects_blank_event_id() -> None:
    state = make_state(status=RiskLimitStatus.WARNING)

    with pytest.raises(
        ValueError,
        match="event_id must not be empty",
    ):
        RiskEvent.from_state(
            event_id="",
            state=state,
            timestamp=TIMESTAMP,
        )


def test_event_rejects_negative_current_value() -> None:
    with pytest.raises(
        ValueError,
        match="current_value must not be negative",
    ):
        RiskEvent(
            event_id="risk-1",
            event_type=RiskEventType.LIMIT_WARNING,
            symbol="BTC",
            limit_type=RiskLimitType.MAX_POSITION,
            status=RiskLimitStatus.WARNING,
            threshold=Decimal("100"),
            warning_threshold=Decimal("80"),
            current_value=Decimal("-1"),
            timestamp=TIMESTAMP,
        )


def test_event_is_immutable() -> None:
    state = make_state(status=RiskLimitStatus.WARNING)

    event = RiskEvent.from_state(
        event_id="risk-1",
        state=state,
        timestamp=TIMESTAMP,
    )

    with pytest.raises(AttributeError):
        event.current_value = Decimal("90")
