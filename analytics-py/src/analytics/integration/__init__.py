"""Gateway integration contracts for the analytics service."""

from analytics.integration.gateway_message import (
    GatewayTradeMessage,
    GatewayMessageParseError,
)

__all__ = [
    "GatewayMessageParseError",
    "GatewayTradeMessage",
]
