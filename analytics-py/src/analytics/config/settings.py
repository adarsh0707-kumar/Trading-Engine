"""Runtime configuration for the analytics service."""

from __future__ import annotations

import os
from dataclasses import dataclass


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

    @classmethod
    def from_environment(cls) -> Settings:
        """Create settings from environment variables."""

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
        )


__all__ = ["Settings"]
