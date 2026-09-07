# ADR-004: Use Node.js as the WebSocket API Gateway

- **Status:** Accepted
- **Date:** 2026-09-07
- **Scope:** Browser communication

---

## 1. Context

The dashboard must display continuously changing information:

- prices;
- trades;
- order-book updates;
- VWAP;
- moving averages;
- PnL;
- risk metrics;
- engine status.

Traditional REST polling would require the browser to repeatedly request new data.

For example:

    Browser → GET /market
    Browser → GET /market
    Browser → GET /market
    Browser → GET /market

This introduces unnecessary requests and latency.

---

## 2. Decision

Node.js will expose a WebSocket server.

The browser will establish one persistent connection:

    React
      │
      │ WebSocket
      ↓
    Node Gateway
      │
      ↓
    Analytics
      │
      ↓
    C++ Engine

The gateway will broadcast relevant events to connected clients.

---

## 3. Responsibilities

The gateway will handle:

- WebSocket connections;
- client registration;
- broadcasting;
- authentication;
- authorization;
- REST endpoints;
- request validation;
- rate limiting;
- service health;
- error handling.

The gateway will NOT implement the matching engine.

---

## 4. WebSocket Event Model

Example:

    {
      "event": "trade",
      "data": {
        "symbol": "SIMBANK",
        "price": 102.45,
        "quantity": 100
      }
    }

Potential events:

- `market_tick`
- `trade`
- `order_book`
- `analytics_update`
- `engine_status`
- `error`

---

## 5. Why Node.js

Node.js provides:

- asynchronous networking;
- mature WebSocket libraries;
- TypeScript support;
- simple integration with React;
- efficient handling of many concurrent connections.

---

## 6. Alternatives Considered

### REST Polling

Rejected because it creates unnecessary traffic and delayed updates.

### Server-Sent Events

Useful for one-way streaming, but WebSockets provide bidirectional communication needed for engine controls.

### Python WebSocket Server

Technically possible, but would mix analytics and browser-facing concerns.

### C++ WebSocket Server

Would unnecessarily increase the responsibility of the performance-critical engine.

---

## 7. Backpressure

The gateway must account for clients that consume data slower than the server produces it.

Possible strategies:

- bounded per-client queues;
- message dropping for obsolete market updates;
- aggregation;
- disconnecting unhealthy clients;
- configurable update frequency.

Not every event must be delivered to every client if the event becomes obsolete.

For example, a dashboard may not need every intermediate price tick.

---

## 8. Consequences

### Positive

- Real-time dashboard.
- Efficient persistent connections.
- Clear browser/backend boundary.
- Easy React integration.

### Negative

- Connection lifecycle management.
- Backpressure handling.
- Authentication complexity.
- Horizontal scaling requires shared state or pub/sub.

---

## 9. Future Scaling

For multiple gateway instances:

    C++ / Python
          |
       Redis/Kafka
          |
    ┌─────┴─────┐
    ↓           ↓
 Gateway A   Gateway B
    ↓           ↓
 Clients      Clients

This allows events to reach clients connected to different gateway instances.