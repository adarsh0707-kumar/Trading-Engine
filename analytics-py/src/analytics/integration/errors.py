"""Failure taxonomy for analytics integration boundaries.

The classes in this module describe *what kind* of failure occurred. Runtime
recovery policies remain owned by the transport/pipeline component that detects
the failure.
"""

from __future__ import annotations

from enum import StrEnum


class FailureCategory(StrEnum):
    """Stable categories used by resilience boundaries."""

    CONNECTION = "connection"
    TIMEOUT = "timeout"
    PROTOCOL = "protocol"
    VALIDATION = "validation"
    QUEUE_OVERFLOW = "queue_overflow"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    PROCESSING = "processing"
    SHUTDOWN = "shutdown"


class IntegrationFailure(Exception):
    """Base exception carrying a stable resilience failure category."""

    category: FailureCategory
    recoverable: bool

    def __init__(
        self,
        message: str,
        *,
        category: FailureCategory,
        recoverable: bool,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.recoverable = recoverable


class ConnectionFailure(IntegrationFailure):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            category=FailureCategory.CONNECTION,
            recoverable=True,
        )


class TimeoutFailure(IntegrationFailure):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            category=FailureCategory.TIMEOUT,
            recoverable=True,
        )


class ProtocolFailure(IntegrationFailure):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            category=FailureCategory.PROTOCOL,
            recoverable=False,
        )


class ValidationFailure(IntegrationFailure):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            category=FailureCategory.VALIDATION,
            recoverable=False,
        )


class QueueOverflow(IntegrationFailure):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            category=FailureCategory.QUEUE_OVERFLOW,
            recoverable=True,
        )


class DependencyUnavailable(IntegrationFailure):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            category=FailureCategory.DEPENDENCY_UNAVAILABLE,
            recoverable=True,
        )


class ProcessingFailure(IntegrationFailure):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            category=FailureCategory.PROCESSING,
            recoverable=False,
        )


class ShutdownFailure(IntegrationFailure):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            category=FailureCategory.SHUTDOWN,
            recoverable=False,
        )


__all__ = [
    "ConnectionFailure",
    "DependencyUnavailable",
    "FailureCategory",
    "IntegrationFailure",
    "ProcessingFailure",
    "ProtocolFailure",
    "QueueOverflow",
    "ShutdownFailure",
    "TimeoutFailure",
    "ValidationFailure",
]
