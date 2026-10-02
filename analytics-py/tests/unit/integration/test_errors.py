from analytics.integration.errors import (
    ConnectionFailure,
    DependencyUnavailable,
    FailureCategory,
    IntegrationFailure,
    ProcessingFailure,
    ProtocolFailure,
    QueueOverflow,
    ShutdownFailure,
    TimeoutFailure,
    ValidationFailure,
)


def test_failure_categories_are_stable() -> None:
    assert [category.value for category in FailureCategory] == [
        "connection",
        "timeout",
        "protocol",
        "validation",
        "queue_overflow",
        "dependency_unavailable",
        "processing",
        "shutdown",
    ]


def test_failure_types_expose_category_and_recoverability() -> None:
    cases = [
        (ConnectionFailure("x"), FailureCategory.CONNECTION, True),
        (TimeoutFailure("x"), FailureCategory.TIMEOUT, True),
        (ProtocolFailure("x"), FailureCategory.PROTOCOL, False),
        (ValidationFailure("x"), FailureCategory.VALIDATION, False),
        (QueueOverflow("x"), FailureCategory.QUEUE_OVERFLOW, True),
        (
            DependencyUnavailable("x"),
            FailureCategory.DEPENDENCY_UNAVAILABLE,
            True,
        ),
        (ProcessingFailure("x"), FailureCategory.PROCESSING, False),
        (ShutdownFailure("x"), FailureCategory.SHUTDOWN, False),
    ]

    for error, category, recoverable in cases:
        assert isinstance(error, IntegrationFailure)
        assert error.category is category
        assert error.recoverable is recoverable
        assert str(error) == "x"
