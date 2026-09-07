# API Reference

## 1. API Overview

The Node.js gateway is the public application boundary.

Base URL:

```text
http://localhost:<GATEWAY_PORT>
```

WebSocket:

```text
ws://localhost:<GATEWAY_PORT>/ws
```

Exact port numbers should be defined in the deployment configuration rather than hard-coded in this document.

---

## 2. Health

### GET `/health`

Returns gateway health.

Example response:

```json
{
  "status": "ok",
  "service": "gateway",
  "timestamp": "2026-09-07T12:00:00.000Z"
}
```

### GET `/health/services`

Returns dependency status.

```json
{
  "gateway": "ok",
  "engine": "ok",
  "analytics": "ok"
}
```

HTTP status should be non-2xx when a required dependency is unavailable.

---

## 3. Simulation Status

### GET `/api/v1/simulation/status`

Response:

```json
{
  "state": "RUNNING",
  "started_at": "2026-09-07T12:00:00.000Z",
  "events_processed": 50000,
  "events_per_second": 17500
}
```

---

## 4. Start Simulation

### POST `/api/v1/simulation/start`

Request:

```json
{
  "seed": 42,
  "speed": 1.0
}
```

Response:

```json
{
  "state": "STARTING"
}
```

If already running, return an appropriate conflict response.

---

## 5. Stop Simulation

### POST `/api/v1/simulation/stop`

Response:

```json
{
  "state": "STOPPING"
}
```

The endpoint should be idempotent where practical.

---

## 6. Configuration

### GET `/api/v1/simulation/config`

Example:

```json
{
  "symbol": "SIM",
  "seed": 42,
  "speed": 1.0,
  "analytics_window": 20
}
```

### PATCH `/api/v1/simulation/config`

Example request:

```json
{
  "speed": 2.0,
  "analytics_window": 30
}
```

The gateway must validate all values.

---

## 7. Metrics

### GET `/api/v1/metrics/current`

Response:

```json
{
  "price": 101.25,
  "vwap": 101.12,
  "sma": 101.08,
  "ema": 101.15,
  "position": 150,
  "realized_pnl": 125.50,
  "unrealized_pnl": 62.25,
  "drawdown": 18.40
}
```

---

## 8. Historical Summary

### GET `/api/v1/metrics/summary`

Possible response:

```json
{
  "event_count": 100000,
  "trade_count": 42150,
  "average_trade_price": 101.11,
  "total_volume": 1200000,
  "max_drawdown": 85.20
}
```

The MVP may calculate this from an in-memory bounded history. Persistent storage can be added later.

---

## 9. WebSocket

### Endpoint

```text
/ws
```

After connection, the server may send:

```json
{
  "type": "connected",
  "connection_id": "conn-123"
}
```

Live event:

```json
{
  "type": "analytics_update",
  "data": {
    "price": 101.25,
    "vwap": 101.12,
    "sma": 101.08,
    "ema": 101.15
  }
}
```

Status event:

```json
{
  "type": "simulation_status",
  "data": {
    "state": "RUNNING"
  }
}
```

---

## 10. Client Commands

Browser clients may send:

```json
{
  "type": "ping"
}
```

Response:

```json
{
  "type": "pong"
}
```

Control operations should normally remain REST operations rather than arbitrary WebSocket commands.

---

## 11. Error Format

All REST errors should use a consistent format:

```json
{
  "error": {
    "code": "INVALID_ARGUMENT",
    "message": "speed must be greater than zero",
    "request_id": "req-123"
  }
}
```

Recommended codes:

```text
INVALID_ARGUMENT
UNAUTHORIZED
FORBIDDEN
NOT_FOUND
CONFLICT
DEPENDENCY_UNAVAILABLE
INTERNAL_ERROR
```

---

## 12. Authentication

For a local MVP, authentication may be disabled.

If enabled:

```text
Authorization: Bearer <token>
```

Control endpoints must require authorization.

Read-only health endpoints may remain public inside a trusted development environment.

---

## 13. Rate Limiting

Control endpoints should have stricter limits than read endpoints.

Example policy:

```text
POST /start       10 requests/minute
POST /stop        10 requests/minute
PATCH /config     30 requests/minute
GET endpoints     higher limit
```

These are initial design values and should be configurable.

---

## 14. CORS

Only configured frontend origins should be allowed.

Development:

```text
http://localhost:<dashboard-port>
```

Production deployments should use explicit HTTPS origins.

---

## 15. API Versioning

All application APIs use:

```text
/api/v1/...
```

Breaking changes should introduce:

```text
/api/v2/...
```

---

## 16. Internal Protocol

The C++ and Python services should not expose their internal ports publicly.

Example:

```text
C++ -> private engine channel
Python -> private analytics channel
Gateway -> public application boundary
```

---

## 17. API Contract Testing

API tests should verify:

- status codes,
- required fields,
- data types,
- error structure,
- authorization behavior,
- WebSocket event structure.

Contract fixtures should be kept under a shared test directory when practical.
