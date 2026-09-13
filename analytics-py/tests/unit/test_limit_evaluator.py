"""Unit tests for risk-limit evaluation."""

from decimal import Decimal

import pytest

from analytics.config.risk_limits import RiskLimitConfig
from analytics.models.risk_limit import RiskLimitStatus, RiskLimitType
from analytics.risk.limit_evaluator import RiskLimitEvaluator
from analytics.risk.risk_manager import RiskSnapshot


def make_snapshot(
    *,
    position: int = 0,
    drawdown: str = "0",
) -> RiskSnapshot:
    """Build a risk snapshot for evaluator tests."""
    drawdown_value = Decimal(drawdown)
    equity = Decimal("100000") - drawdown_value

    return RiskSnapshot(
        position=position,
        average_entry_price=Decimal("100") if position else None,
        realized_pnl=Decimal("0"),
        unrealized_pnl=Decimal("0"),
        equity=equity,
        peak_equity=Decimal("100000"),
        drawdown=drawdown_value,
    )


def test_evaluator_returns_ok_below_warning_threshold() -> None:
    """Values below the warning threshold should be OK."""
    config = RiskLimitConfig(
        max_position=100,
        warning_ratio=Decimal("0.80"),
    )

    evaluator = RiskLimitEvaluator(config)

    states = evaluator.evaluate(
        snapshot=make_snapshot(position=50),
        market_price=Decimal("100"),
    )

    assert len(states) == 1
    assert states[0].limit.limit_type == RiskLimitType.MAX_POSITION
    assert states[0].limit.threshold == Decimal("100")
    assert states[0].limit.warning_threshold == Decimal("80")
    assert states[0].current_value == Decimal("50")
    assert states[0].status == RiskLimitStatus.OK


def test_evaluator_returns_warning_at_warning_threshold() -> None:
    """Values at the warning threshold should be WARNING."""
    config = RiskLimitConfig(
        max_position=100,
        warning_ratio=Decimal("0.80"),
    )

    evaluator = RiskLimitEvaluator(config)

    states = evaluator.evaluate(
        snapshot=make_snapshot(position=80),
        market_price=Decimal("100"),
    )

    assert states[0].current_value == Decimal("80")
    assert states[0].status == RiskLimitStatus.WARNING


def test_evaluator_returns_breached_at_limit() -> None:
    """Values at or above the limit should be BREACHED."""
    config = RiskLimitConfig(
        max_position=100,
    )

    evaluator = RiskLimitEvaluator(config)

    states = evaluator.evaluate(
        snapshot=make_snapshot(position=100),
        market_price=Decimal("100"),
    )

    assert states[0].current_value == Decimal("100")
    assert states[0].status == RiskLimitStatus.BREACHED


def test_position_limit_uses_absolute_position() -> None:
    """Short positions should be evaluated by absolute quantity."""
    config = RiskLimitConfig(max_position=100)

    evaluator = RiskLimitEvaluator(config)

    states = evaluator.evaluate(
        snapshot=make_snapshot(position=-90),
        market_price=Decimal("100"),
    )

    assert states[0].current_value == Decimal("90")
    assert states[0].status == RiskLimitStatus.WARNING


def test_position_value_uses_absolute_mark_to_market_value() -> None:
    """Position value should use absolute signed position value."""
    config = RiskLimitConfig(
        max_position_value=Decimal("10000"),
    )

    evaluator = RiskLimitEvaluator(config)

    states = evaluator.evaluate(
        snapshot=make_snapshot(position=-100),
        market_price=Decimal("80"),
    )

    assert states[0].limit.limit_type == RiskLimitType.MAX_POSITION_VALUE
    assert states[0].current_value == Decimal("8000")
    assert states[0].status == RiskLimitStatus.WARNING


def test_drawdown_limit_is_evaluated() -> None:
    """Drawdown should be evaluated directly from the risk snapshot."""
    config = RiskLimitConfig(
        max_drawdown=Decimal("10000"),
    )

    evaluator = RiskLimitEvaluator(config)

    states = evaluator.evaluate(
        snapshot=make_snapshot(drawdown="8500"),
        market_price=Decimal("100"),
    )

    assert states[0].limit.limit_type == RiskLimitType.MAX_DRAWDOWN
    assert states[0].current_value == Decimal("8500")
    assert states[0].status == RiskLimitStatus.WARNING


def test_daily_loss_limit_is_evaluated() -> None:
    """Daily loss should be evaluated as an absolute loss amount."""
    config = RiskLimitConfig(
        max_daily_loss=Decimal("5000"),
    )

    evaluator = RiskLimitEvaluator(config)

    states = evaluator.evaluate(
        snapshot=make_snapshot(),
        market_price=Decimal("100"),
        daily_loss=Decimal("5000"),
    )

    assert states[0].limit.limit_type == RiskLimitType.MAX_DAILY_LOSS
    assert states[0].current_value == Decimal("5000")
    assert states[0].status == RiskLimitStatus.BREACHED


def test_disabled_limits_are_not_returned() -> None:
    """Disabled limits should not produce risk-limit states."""
    config = RiskLimitConfig()

    evaluator = RiskLimitEvaluator(config)

    states = evaluator.evaluate(
        snapshot=make_snapshot(position=100),
        market_price=Decimal("100"),
        daily_loss=Decimal("1000"),
    )

    assert states == ()


def test_all_enabled_limits_are_evaluated() -> None:
    """All configured limits should produce states in deterministic order."""
    config = RiskLimitConfig(
        max_position=100,
        max_position_value=Decimal("10000"),
        max_drawdown=Decimal("5000"),
        max_daily_loss=Decimal("2500"),
    )

    evaluator = RiskLimitEvaluator(config)

    states = evaluator.evaluate(
        snapshot=make_snapshot(
            position=100,
            drawdown="5000",
        ),
        market_price=Decimal("100"),
        daily_loss=Decimal("2500"),
    )

    assert [state.limit.limit_type for state in states] == [
        RiskLimitType.MAX_POSITION,
        RiskLimitType.MAX_POSITION_VALUE,
        RiskLimitType.MAX_DRAWDOWN,
        RiskLimitType.MAX_DAILY_LOSS,
    ]

    assert [state.status for state in states] == [
        RiskLimitStatus.BREACHED,
        RiskLimitStatus.BREACHED,
        RiskLimitStatus.BREACHED,
        RiskLimitStatus.BREACHED,
    ]


def test_symbol_is_attached_to_evaluated_limits() -> None:
    """Evaluated limits should retain the optional symbol."""
    config = RiskLimitConfig(max_position=100)

    evaluator = RiskLimitEvaluator(config)

    states = evaluator.evaluate(
        snapshot=make_snapshot(position=50),
        market_price=Decimal("100"),
        symbol="RELIANCE",
    )

    assert states[0].limit.symbol == "RELIANCE"


@pytest.mark.parametrize(
    ("market_price", "daily_loss", "message"),
    [
        (
            Decimal("0"),
            Decimal("0"),
            "market_price must be greater than zero",
        ),
        (
            Decimal("-1"),
            Decimal("0"),
            "market_price must be greater than zero",
        ),
        (
            Decimal("100"),
            Decimal("-1"),
            "daily_loss must not be negative",
        ),
    ],
)
def test_invalid_evaluation_inputs(
    market_price: Decimal,
    daily_loss: Decimal,
    message: str,
) -> None:
    """Invalid evaluator inputs should fail clearly."""
    evaluator = RiskLimitEvaluator(
        RiskLimitConfig(max_position=100)
    )

    with pytest.raises(ValueError, match=message):
        evaluator.evaluate(
            snapshot=make_snapshot(),
            market_price=market_price,
            daily_loss=daily_loss,
        )


def test_blank_symbol_is_rejected() -> None:
    """Blank symbols should not be accepted."""
    evaluator = RiskLimitEvaluator(
        RiskLimitConfig(max_position=100)
    )

    with pytest.raises(ValueError, match="symbol must not be blank"):
        evaluator.evaluate(
            snapshot=make_snapshot(),
            market_price=Decimal("100"),
            symbol="   ",
        )
