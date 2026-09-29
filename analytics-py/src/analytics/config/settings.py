"""Runtime configuration for the analytics service."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass


class ConfigurationError(ValueError):
    """Raised when analytics service configuration is invalid."""


@dataclass(frozen=True)
class Settings:
    """Analytics service runtime settings."""

    engine_host: str = "127.0.0.1"
    engine_port: int = 9000

    connect_timeout: float = 5.0
    receive_timeout: float = 1.0

    reconnect: bool = True
    reconnect_delay: float = 1.0

    max_payload_size: int = 1024 * 1024
    backpressure_queue_capacity: int = 1000
    backpressure_enqueue_timeout: float = 0.1

    persistence_retry_attempts: int = 2
    persistence_retry_delay: float = 0.1
    publish_retry_attempts: int = 2
    publish_retry_delay: float = 0.1

    log_level: str = "INFO"
    log_format: str = (
        "%(asctime)s %(levelname)s %(name)s "
        "[%(threadName)s] %(message)s"
    )

    database_url: str | None = None

    metrics_host: str = "0.0.0.0"
    metrics_port: int | None = None

    def __post_init__(self) -> None:
        """Validate all runtime settings at construction time."""
        if not self.engine_host.strip():
            raise ConfigurationError("engine_host must not be empty")
        self._validate_port("engine_port", self.engine_port)
        self._validate_positive_finite("connect_timeout", self.connect_timeout)
        self._validate_positive_finite("receive_timeout", self.receive_timeout)
        if self.reconnect_delay < 0 or not math.isfinite(self.reconnect_delay):
            raise ConfigurationError(
                "reconnect_delay must be a finite number greater than or equal to 0"
            )
        if self.max_payload_size <= 0:
            raise ConfigurationError("max_payload_size must be greater than 0")
        if isinstance(self.backpressure_queue_capacity, bool) or not isinstance(self.backpressure_queue_capacity, int) or self.backpressure_queue_capacity <= 0:
            raise ConfigurationError("backpressure_queue_capacity must be an integer greater than 0")
        if not isinstance(self.backpressure_enqueue_timeout, (int, float)) or isinstance(self.backpressure_enqueue_timeout, bool) or self.backpressure_enqueue_timeout < 0 or not math.isfinite(self.backpressure_enqueue_timeout):
            raise ConfigurationError("backpressure_enqueue_timeout must be a finite number greater than or equal to 0")
        if isinstance(self.persistence_retry_attempts, bool) or not isinstance(self.persistence_retry_attempts, int) or self.persistence_retry_attempts < 0:
            raise ConfigurationError("persistence_retry_attempts must be an integer greater than or equal to 0")
        if not isinstance(self.persistence_retry_delay, (int, float)) or isinstance(self.persistence_retry_delay, bool) or self.persistence_retry_delay < 0 or not math.isfinite(self.persistence_retry_delay):
            raise ConfigurationError("persistence_retry_delay must be a finite number greater than or equal to 0")
        if isinstance(self.publish_retry_attempts, bool) or not isinstance(self.publish_retry_attempts, int) or self.publish_retry_attempts < 0:
            raise ConfigurationError("publish_retry_attempts must be an integer greater than or equal to 0")
        if not isinstance(self.publish_retry_delay, (int, float)) or isinstance(self.publish_retry_delay, bool) or self.publish_retry_delay < 0 or not math.isfinite(self.publish_retry_delay):
            raise ConfigurationError("publish_retry_delay must be a finite number greater than or equal to 0")
        if not self.log_level.strip():
            raise ConfigurationError("log_level must not be empty")
        if not self.log_format:
            raise ConfigurationError("log_format must not be empty")
        if self.database_url is not None and not self.database_url.strip():
            raise ConfigurationError("database_url must not be empty when provided")
        if not self.metrics_host.strip():
            raise ConfigurationError("metrics_host must not be empty")
        if self.metrics_port is not None:
            self._validate_port("metrics_port", self.metrics_port)

    @staticmethod
    def _validate_port(name: str, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfigurationError(f"{name} must be an integer between 1 and 65535")
        if not 1 <= value <= 65535:
            raise ConfigurationError(f"{name} must be between 1 and 65535")

    @staticmethod
    def _validate_positive_finite(name: str, value: float) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ConfigurationError(f"{name} must be a finite number greater than 0")
        if value <= 0 or not math.isfinite(value):
            raise ConfigurationError(f"{name} must be a finite number greater than 0")

    @classmethod
    def from_environment(cls) -> Settings:
        """Create settings from environment variables."""

        metrics_port_value = os.getenv("TRADING_ENGINE_METRICS_PORT")

        return cls(
            engine_host=os.getenv(
                "TRADING_ENGINE_HOST",
                "127.0.0.1",
            ),
            engine_port=int(
                os.getenv(
                    "TRADING_ENGINE_PORT",
                    "9000",
                )
            ),
            connect_timeout=float(
                os.getenv(
                    "TRADING_ENGINE_CONNECT_TIMEOUT",
                    "5.0",
                )
            ),
            receive_timeout=float(
                os.getenv(
                    "TRADING_ENGINE_RECEIVE_TIMEOUT",
                    "1.0",
                )
            ),
            reconnect=os.getenv(
                "TRADING_ENGINE_RECONNECT",
                "true",
            ).lower()
            in {"1", "true", "yes", "on"},
            reconnect_delay=float(
                os.getenv(
                    "TRADING_ENGINE_RECONNECT_DELAY",
                    "1.0",
                )
            ),
            max_payload_size=int(
                os.getenv(
                    "TRADING_ENGINE_MAX_PAYLOAD_SIZE",
                    str(1024 * 1024),
                )
            ),
            database_url=os.getenv(
                "TRADING_ENGINE_DATABASE_URL",
            ),
            backpressure_queue_capacity=int(os.getenv("TRADING_ENGINE_BACKPRESSURE_QUEUE_CAPACITY", "1000")),
            backpressure_enqueue_timeout=float(os.getenv("TRADING_ENGINE_BACKPRESSURE_ENQUEUE_TIMEOUT", "0.1")),
            persistence_retry_attempts=int(os.getenv("TRADING_ENGINE_PERSISTENCE_RETRY_ATTEMPTS", "2")),
            persistence_retry_delay=float(os.getenv("TRADING_ENGINE_PERSISTENCE_RETRY_DELAY", "0.1")),
            publish_retry_attempts=int(os.getenv("TRADING_ENGINE_PUBLISH_RETRY_ATTEMPTS", "2")),
            publish_retry_delay=float(os.getenv("TRADING_ENGINE_PUBLISH_RETRY_DELAY", "0.1")),
            log_level=os.getenv("TRADING_ENGINE_LOG_LEVEL", "INFO"),
            log_format=os.getenv(
                "TRADING_ENGINE_LOG_FORMAT",
                "%(asctime)s %(levelname)s %(name)s "
                "[%(threadName)s] %(message)s",
            ),
            metrics_host=os.getenv(
                "TRADING_ENGINE_METRICS_HOST",
                "0.0.0.0",
            ),
            metrics_port=(
                int(metrics_port_value)
                if metrics_port_value
                else None
            ),
        )


__all__ = ["ConfigurationError", "Settings"]
