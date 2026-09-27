"""Contract tests for database-agnostic persistence repositories."""

from __future__ import annotations

import inspect
from datetime import datetime
from typing import get_type_hints

from inspect import Parameter

from analytics.persistence.repositories import (
    AnalyticsRepository,
    PositionRepository,
    RiskRepository,
    TradeRepository,
)
from analytics.risk.risk_manager import RiskSnapshot

from analytics.models import AnalyticsResult, Trade, RiskEvent


def _assert_methods(repository: type, expected_methods: dict[str, dict]) -> None:
    """Verify that a repository exposes the expected contract methods."""

    for method_name, expected in expected_methods.items():
        method = getattr(repository, method_name, None)

        assert method is not None, (
            f"{repository.__name__} is missing method {method_name}"
        )

        signature = inspect.signature(method)
        parameters = list(signature.parameters.values())

        expected_parameter_names = expected["parameters"]

        assert [
            parameter.name for parameter in parameters
        ] == expected_parameter_names

        hints = get_type_hints(method)

        assert hints["return"] == expected["return"]


def test_trade_repository_contract() -> None:
    """TradeRepository exposes the required persistence contract."""

    _assert_methods(
        TradeRepository,
        {
            "save": {
                "parameters": ["self", "trade"],
                "return": type(None),
            },
            "get_by_id": {
                "parameters": ["self", "trade_id"],
                "return": Trade | None,
            },
            "list_by_symbol": {
                "parameters": ["self", "symbol"],
                "return": tuple[Trade, ...],
            },
            "list_by_time_range": {
                "parameters": ["self", "start", "end"],
                "return": tuple[Trade, ...],
            },
        },
    )


def test_trade_repository_parameter_annotations() -> None:
    """TradeRepository parameters use the expected domain types."""

    assert get_type_hints(TradeRepository.save)["trade"] == Trade
    assert get_type_hints(TradeRepository.get_by_id)["trade_id"] == str
    assert get_type_hints(TradeRepository.list_by_symbol)["symbol"] == str

    hints = get_type_hints(TradeRepository.list_by_time_range)
    assert hints["start"] == datetime
    assert hints["end"] == datetime


def test_analytics_repository_contract() -> None:
    """AnalyticsRepository exposes the required persistence contract."""

    _assert_methods(
        AnalyticsRepository,
        {
            "save": {
                "parameters": ["self", "result"],
                "return": type(None),
            },
            "get_by_event_id": {
                "parameters": ["self", "event_id"],
                "return": AnalyticsResult | None,
            },
            "list_by_symbol": {
                "parameters": ["self", "symbol"],
                "return": tuple[AnalyticsResult, ...],
            },
            "list_by_time_range": {
                "parameters": ["self", "start", "end"],
                "return": tuple[AnalyticsResult, ...],
            },
        },
    )


def test_analytics_repository_parameter_annotations() -> None:
    """AnalyticsRepository parameters use the expected domain types."""

    assert get_type_hints(AnalyticsRepository.save)["result"] == AnalyticsResult
    assert get_type_hints(AnalyticsRepository.get_by_event_id)["event_id"] == str
    assert get_type_hints(AnalyticsRepository.list_by_symbol)["symbol"] == str

    hints = get_type_hints(AnalyticsRepository.list_by_time_range)
    assert hints["start"] == datetime
    assert hints["end"] == datetime


def test_position_repository_contract() -> None:
    """PositionRepository exposes the required persistence contract."""

    _assert_methods(
        PositionRepository,
        {
            "save": {
                "parameters": ["self", "symbol", "snapshot"],
                "return": type(None),
            },
            "get_by_symbol": {
                "parameters": ["self", "symbol"],
                "return": RiskSnapshot | None,
            },
        },
    )


def test_position_repository_parameter_annotations() -> None:
    """PositionRepository parameters use the expected domain types."""

    save_hints = get_type_hints(PositionRepository.save)

    assert save_hints["symbol"] == str
    assert save_hints["snapshot"] == RiskSnapshot

    get_hints = get_type_hints(PositionRepository.get_by_symbol)

    assert get_hints["symbol"] == str
    assert get_hints["return"] == RiskSnapshot | None


def test_risk_repository_contract() -> None:
    """RiskRepository exposes the required persistence contract."""

    _assert_methods(
        RiskRepository,
        {
            "save_risk_state": {
                "parameters": ["self", "symbol", "snapshot"],
                "return": type(None),
            },
            "save_event": {
                "parameters": ["self", "event"],
                "return": type(None),
            },
            "get_latest_state": {
                "parameters": ["self", "symbol"],
                "return": RiskSnapshot | None,
            },
            "list_events": {
                "parameters": ["self", "symbol"],
                "return": tuple[RiskEvent, ...],
            },
            "list_events_by_time_range": {
                "parameters": ["self", "symbol", "start", "end"],
                "return": tuple[RiskEvent, ...],
            },
        },
    )


def test_risk_repository_parameter_annotations() -> None:
    """RiskRepository parameters use the expected domain types."""

    save_state_hints = get_type_hints(RiskRepository.save_risk_state)

    assert save_state_hints["symbol"] == str
    assert save_state_hints["snapshot"] == RiskSnapshot

    save_event_hints = get_type_hints(RiskRepository.save_event)

    from analytics.models.risk_event import RiskEvent

    assert save_event_hints["event"] == RiskEvent

    latest_state_hints = get_type_hints(RiskRepository.get_latest_state)

    assert latest_state_hints["symbol"] == str
    assert latest_state_hints["return"] == RiskSnapshot | None

    list_hints = get_type_hints(RiskRepository.list_events)

    assert list_hints["symbol"] == str

    range_hints = get_type_hints(
        RiskRepository.list_events_by_time_range,
    )

    assert range_hints["symbol"] == str
    assert range_hints["start"] == datetime
    assert range_hints["end"] == datetime


def test_persistence_package_exports() -> None:
    """The persistence package exports all repository contracts."""

    from analytics.persistence import repositories

    assert repositories.TradeRepository is TradeRepository
    assert repositories.AnalyticsRepository is AnalyticsRepository
    assert repositories.PositionRepository is PositionRepository
    assert repositories.RiskRepository is RiskRepository

def test_position_repository_requires_keyword_arguments() -> None:
    """PositionRepository uses keyword-only arguments."""

    save_signature = inspect.signature(PositionRepository.save)
    get_signature = inspect.signature(PositionRepository.get_by_symbol)

    assert save_signature.parameters["symbol"].kind is Parameter.KEYWORD_ONLY
    assert save_signature.parameters["snapshot"].kind is Parameter.KEYWORD_ONLY
    assert get_signature.parameters["symbol"].kind is Parameter.KEYWORD_ONLY


def test_risk_repository_requires_keyword_arguments() -> None:
    """RiskRepository uses keyword-only arguments."""

    save_state_signature = inspect.signature(
        RiskRepository.save_risk_state,
    )
    save_event_signature = inspect.signature(
        RiskRepository.save_event,
    )
    latest_state_signature = inspect.signature(
        RiskRepository.get_latest_state,
    )
    list_events_signature = inspect.signature(
        RiskRepository.list_events,
    )
    list_range_signature = inspect.signature(
        RiskRepository.list_events_by_time_range,
    )

    assert (
        save_state_signature.parameters["symbol"].kind
        is Parameter.KEYWORD_ONLY
    )
    assert (
        save_state_signature.parameters["snapshot"].kind
        is Parameter.KEYWORD_ONLY
    )

    assert (
        save_event_signature.parameters["event"].kind
        is Parameter.KEYWORD_ONLY
    )

    assert (
        latest_state_signature.parameters["symbol"].kind
        is Parameter.KEYWORD_ONLY
    )

    assert (
        list_events_signature.parameters["symbol"].kind
        is Parameter.KEYWORD_ONLY
    )

    assert (
        list_range_signature.parameters["symbol"].kind
        is Parameter.KEYWORD_ONLY
    )
    assert (
        list_range_signature.parameters["start"].kind
        is Parameter.KEYWORD_ONLY
    )
    assert (
        list_range_signature.parameters["end"].kind
        is Parameter.KEYWORD_ONLY
    )