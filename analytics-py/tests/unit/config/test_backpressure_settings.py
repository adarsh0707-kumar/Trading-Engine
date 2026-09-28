"""Tests for backpressure configuration."""

import math

import pytest

from analytics.config import ConfigurationError, Settings


@pytest.mark.parametrize("capacity", [0, -1, True, 1.5])
def test_invalid_backpressure_queue_capacity(capacity: object) -> None:
    with pytest.raises(ConfigurationError):
        Settings(backpressure_queue_capacity=capacity)  # type: ignore[arg-type]


@pytest.mark.parametrize("timeout", [-0.1, math.inf, -math.inf])
def test_invalid_backpressure_enqueue_timeout(timeout: float) -> None:
    with pytest.raises(ConfigurationError):
        Settings(backpressure_enqueue_timeout=timeout)


def test_backpressure_configuration_accepts_zero_timeout() -> None:
    settings = Settings(
        backpressure_queue_capacity=10,
        backpressure_enqueue_timeout=0,
    )

    assert settings.backpressure_queue_capacity == 10
    assert settings.backpressure_enqueue_timeout == 0
