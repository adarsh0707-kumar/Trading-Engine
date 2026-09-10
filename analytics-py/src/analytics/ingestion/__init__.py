"""Market-data ingestion components."""

from analytics.ingestion.socket_client import (
    SocketClient,
    SocketProtocolError,
)

__all__ = [
    "SocketClient",
    "SocketProtocolError",
]
