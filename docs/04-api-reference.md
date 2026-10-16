# API Reference

## 1. API Overview

The Node.js gateway is the public application boundary for the trading-engine system.

Base URL:

```text
http://localhost:<GATEWAY_PORT>
```

The gateway exposes a versioned application API under `/api/v1`.

WebSocket support is implemented at `/ws` for live dashboard events. Clients explicitly subscribe to supported event types and receive normalized Gateway event envelopes.

The engine emits `MARKET_DATA` events independently of trade execution. Each event payload contains `symbol`, `price`, and `sequence`. The gateway publishes these events over WebSocket and updates `GET /api/v1/market` without adding a trade to history. Market-price updates continue while the engine is risk-halted; a halt still prevents matching and trade execution. Subscribe to `MARKET_DATA` for price ticks and `TRADE` for executed trades.

---

## 2. Currently Implemented Endpoints

| Method | Endpoint | Status | Purpose |
| --- | --- | --- | --- |
| GET | `/api/health` | Implemented | Gateway process health |
| GET | `/api/v1/status` | Implemented | Gateway, engine, and analytics dependency status |
| GET | `/api/v1/market` | Implemented | Current market-state contract |
| GET | `/api/v1/orderbook` | Implemented | Current order-book contract |
| GET | `/api/v1/trades` | Implemented | Trade-history contract |
| GET | `/api/v1/analytics` | Implemented | Analytics-state contract |
| POST | `/api/v1/engine/start` | Implemented | Engine start control contract |
| POST | `/api/v1/engine/stop` | Implemented | Engine stop control contract |
| POST | `/api/v1/engine/reset` | Implemented | Engine reset control contract |
| GET | `<METRICS_PATH>` | Implemented | Prometheus metrics when enabled |

Phase 4.3 establishes the HTTP API boundary and deterministic dependency behavior. The gateway does not fabricate market, order-book, trade, analytics, or engine state when the corresponding upstream implementation is unavailable.

---

## 3. Gateway Health

### GET `/api/health`

Returns the health of the gateway process.

Example response:

```json
{
  "status": "ok",
  "service": "gateway"
}
```

The health endpoint does not currently report engine or analytics dependency state. Use `/api/v1/status` for that information.

---

## 4. Gateway Status

### GET `/api/v1/status`

Returns the current gateway dependency status.

Example response:

```json
{
  "data": {
    "gateway": "ok",
    "engine": "disconnected",
    "analytics": "disconnected"
  }
}
```

Possible dependency states:

```text
connected
disconnected
```

The current default provider reports the engine and analytics dependencies as disconnected until their real integrations are connected.

---

## 5. Market

### GET `/api/v1/market`

Returns the latest market-state snapshot when a market provider is available.

Example response:

```json
{
  "data": {
    "symbol": "BTC-USD",
    "lastPrice": 65000.5,
    "lastQuantity": 0.25,
    "timestamp": "2026-09-30T12:00:00.000Z"
  }
}
```

If no market provider data is available:

```http
503 Service Unavailable
```

```json
{
  "error": {
    "code": "DEPENDENCY_UNAVAILABLE",
    "message": "Market state is unavailable",
    "request_id": "<request-id>"
  }
}
```

---

## 6. Order Book

### GET `/api/v1/orderbook`

Returns the latest live order-book snapshot obtained by the Gateway from the C++ Engine.

Example response:

```json
{
  "data": {
    "symbol": "BTC-USD",
    "bids": [
      {
        "price": 64999.5,
        "quantity": 1.25
      }
    ],
    "asks": [
      {
        "price": 65000.5,
        "quantity": 0.8
      }
    ],
    "timestamp": "2026-09-30T12:00:00.000Z"
  }
}
```

If the C++ Engine order-book snapshot is unavailable or the Gateway cannot obtain a valid snapshot:

```http
503 Service Unavailable
```

```json
{
  "error": {
    "code": "DEPENDENCY_UNAVAILABLE",
    "message": "Order book state is unavailable",
    "request_id": "<request-id>"
  }
}
```

---

## 7. Trades

### GET `/api/v1/trades`

Returns recent trades when a trades provider is available.

Example response:

```json
{
  "data": {
    "trades": [
      {
        "tradeId": "trade-42-buy-41",
        "symbol": "BTC-USD",
        "price": 65000.5,
        "quantity": 0.25,
        "takerSide": "buy",
        "timestamp": "2026-09-30T12:00:00.000Z"
      }
    ]
  }
}
```

If trade data is unavailable:

```http
503 Service Unavailable
```

```json
{
  "error": {
    "code": "DEPENDENCY_UNAVAILABLE",
    "message": "Trade history is unavailable",
    "request_id": "<request-id>"
  }
}
```

---

## 8. Analytics

### GET `/api/v1/analytics`

Returns the latest analytics snapshot when an analytics provider is available.

Example response:

```json
{
  "data": {
    "equity": 100000,
    "realizedPnl": 1250.5,
    "unrealizedPnl": 320.25,
    "drawdown": 0.018,
    "riskStatus": "ok",
    "timestamp": "2026-09-30T12:00:00.000Z"
  }
}
```

Possible risk states:

```text
ok
warning
breached
```

Analytics has two distinct unavailable states:

**1. The Analytics service is disconnected**

The Gateway returns `503 Service Unavailable` with `DEPENDENCY_UNAVAILABLE`:

```json
{
  "error": {
    "code": "DEPENDENCY_UNAVAILABLE",
    "message": "Analytics service is unavailable",
    "request_id": "<request-id>"
  }
}
```

**2. Analytics is connected, but its first snapshot has not arrived**

The Gateway returns `503 Service Unavailable` with `DATA_NOT_READY`:

```json
{
  "error": {
    "code": "DATA_NOT_READY",
    "message": "Analytics is waiting for its first data snapshot",
    "request_id": "<request-id>"
  }
}
```

The dashboard treats `DATA_NOT_READY` as a waiting state rather than a fatal analytics error. A `RISK_EVENT` received before the first `ANALYTICS_UPDATE` may update risk-status tracking, but it must not fabricate an analytics snapshot. The analytics endpoint remains not-ready until a real analytics snapshot is published. Once a snapshot exists, the latest applicable risk status is included in the response.

---

## 9. Engine Control

The engine control endpoints define the HTTP contract for simulation control.

### POST `/api/v1/engine/start`

Requests engine startup.

### POST `/api/v1/engine/stop`

Requests engine shutdown.

### POST `/api/v1/engine/reset`

Requests an engine reset.

These endpoints currently accept an empty request body.

When an `EngineProvider` implementation supports the requested operation, the API returns:

```http
202 Accepted
```

Example:

```json
{
  "data": {
    "action": "start",
    "status": "accepted"
  }
}
```

The `action` value is one of:

```text
start
stop
reset
```

If engine control is not available:

```http
503 Service Unavailable
```

```json
{
  "error": {
    "code": "DEPENDENCY_UNAVAILABLE",
    "message": "Engine control is unavailable",
    "request_id": "<request-id>"
  }
}
```

### Current engine integration status

The C++ engine currently exposes local `start()`, `stop()`, and market-generator reset operations, but its network protocol does not yet expose corresponding remote START, STOP, or RESET commands.

Therefore the Phase 4.3 gateway does not invent network commands for these operations.

Network engine-command integration is addressed by the later engine protocol work.

---

## 10. Error Response Contract

API errors use a deterministic JSON structure:

```json
{
  "error": {
    "code": "INVALID_ARGUMENT",
    "message": "Request validation failed",
    "request_id": "req-123"
  }
}
```

The `request_id` is generated from the Fastify request identifier.

### HTTP status mappings

| Status | Error code | Meaning |
| --- | --- | --- |
| 400 | `INVALID_ARGUMENT` | Invalid request or validation failure |
| 404 | `NOT_FOUND` | Requested route/resource was not found |
| 409 | `CONFLICT` | Request conflicts with current state |
| 500 | `INTERNAL_ERROR` | Unexpected gateway error |
| 503 | `DEPENDENCY_UNAVAILABLE` | Required upstream dependency is unavailable |

The API error type also defines `UNAUTHORIZED` and `FORBIDDEN` codes for future authenticated/authorized endpoints.

Unknown routes return:

```http
404 Not Found
```

with:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Route not found",
    "request_id": "<request-id>"
  }
}
```

---

## 11. Prometheus Metrics

### GET `<METRICS_PATH>`

Prometheus metrics are exposed when:

```text
METRICS_ENABLED=true
```

The default configured path is:

```text
/metrics
```

The path can be changed using:

```text
METRICS_PATH
```

When metrics are disabled, the metrics route is not registered and requests return:

```http
404 Not Found
```

---

## 12. CORS

The gateway applies the configured CORS origin at runtime.

Configuration is controlled through:

```text
CORS_ORIGIN
```

The gateway configuration determines which browser origins are permitted.

---

## 13. WebSocket API

### Endpoint

```text
ws://localhost:<GATEWAY_PORT>/ws
```

The Gateway WebSocket is the browser-facing live-event boundary. The dashboard must use this endpoint rather than connecting directly to the Engine or Analytics services.

### Supported event types

```text
MARKET_DATA
TRADE
ANALYTICS_UPDATE
RISK_EVENT
```

`MARKET_DATA` is emitted independently of matching and trade execution. It updates the market snapshot and dashboard price display, including while the engine is risk-halted. It must not be recorded as a trade or forwarded to analytics as a trade. `TRADE` represents an actual execution.

### Subscription message

```json
{
  "action": "subscribe",
  "events": ["MARKET_DATA", "TRADE"]
}
```

Unsubscribe uses the same shape with `action: "unsubscribe"`.

### Control messages

The connection lifecycle may emit `CONNECTION_READY`, `SUBSCRIPTION_UPDATED`, and `ERROR` control messages.

### MARKET_DATA event

`MARKET_DATA` payloads contain the symbol, current simulated price, and monotonically increasing market sequence. The gateway exposes the event through the normalized WebSocket envelope:

```json
{
  "type": "MARKET_DATA",
  "payload": {
    "symbol": "SIM",
    "price": 100.25,
    "sequence": 42
  }
}
```

The market snapshot endpoint (`GET /api/v1/market`) reflects the latest accepted market update. Market updates do not imply that an order matched or a trade occurred.

### TRADE event

TRADE events use the normalized event envelope:

```json
{
  "type": "TRADE",
  "eventId": "evt-123",
  "requestId": "req-123",
  "timestamp": "2026-10-05T12:00:00.000Z",
  "payload": {
    "symbol": "SIM",
    "price": 101.25,
    "quantity": 25,
    "takerOrderId": "order-taker",
    "makerOrderId": "order-maker",
    "takerSide": "BUY",
    "buyOrderId": "order-buy",
    "sellOrderId": "order-sell"
  }
}
```

The dashboard WebSocket client reconnects with bounded backoff and restores subscriptions after reconnect. Malformed messages are rejected safely and must not crash the dashboard.

### Live order-book snapshot path

The `/api/v1/orderbook` endpoint uses the Gateway Engine Event Client to request a `BOOK_SNAPSHOT` from the C++ Engine over the existing 4-byte big-endian framed TCP protocol. The Gateway correlates the response with the request ID, validates the snapshot, and returns the typed order-book response to the dashboard.

The dashboard does not connect directly to the C++ Engine. Best Bid, Best Ask, and Spread shown by the Market Summary are derived from the returned order-book snapshot.

---

## 13. Planned APIs

The following capabilities remain planned and are not currently implemented.

### Simulation Status

```text
GET /api/v1/simulation/status
```

Intended to expose detailed simulation lifecycle state.

### Simulation Configuration

Future endpoints may expose or modify simulation configuration.

The exact contract will be defined when simulation configuration becomes an implemented gateway responsibility.

### Historical Metrics

Historical analytics and metrics query APIs are deferred to Phase 6 unless a minimal read-through contract is required earlier.

### WebSocket API

Live real-time streaming uses the Gateway WebSocket boundary:

```text
ws://localhost:<GATEWAY_PORT>/ws
```

The WebSocket protocol and event contracts are implemented; supported live event types are documented in the WebSocket API section.

---

## 14. Phase 4.3 Contract Boundary

Phase 4.3 establishes:

- `/api/v1` route versioning
- deterministic success response envelopes
- deterministic API error responses
- request identifiers in error responses
- dependency-unavailable mapping
- market, order-book, trade, and analytics provider boundaries
- engine-control provider boundaries
- integration tests for success and dependency-failure behavior
- compatibility with the existing health and metrics endpoints

Phase 4.3 does not fabricate upstream state.

The real engine network protocol integration is handled by the engine protocol phase, while real Python analytics integration is handled by the analytics integration phase.

---

## 15. API Design Conventions

### Success responses

Successful application responses use:

```json
{
  "data": {}
}
```

### Errors

Errors use:

```json
{
  "error": {
    "code": "...",
    "message": "...",
    "request_id": "..."
  }
}
```

### Versioning

Application routes are versioned under:

```text
/api/v1
```

### Dependency failures

Unavailable upstream services are represented explicitly with:

```text
503 DEPENDENCY_UNAVAILABLE
```

This prevents the gateway from presenting fabricated or stale upstream state as real data.
