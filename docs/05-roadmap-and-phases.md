# Roadmap and Implementation Phases

## 1. Strategy

Development follows a vertical-slice approach: each phase produces something executable and testable.

The goal is not to build every abstraction before seeing data on the screen.

---

## Phase 0 — Product Specification

### Objectives

- Freeze MVP scope.
- Define event schemas.
- Define repository structure.
- Define test strategy.
- Define success criteria.

### Deliverables

```text
docs/01-product-requirements.md
docs/02-architecture.md
docs/03-data-model.md
docs/04-api-reference.md
```

### Exit criteria

A developer can explain the complete event journey without reading implementation code.

---

## Phase 1 — C++ Order Book

### Objectives

Implement:

- Order.
- Price level.
- Bid book.
- Ask book.
- Matching engine.
- Trade generation.

### Suggested implementation order

1. Order model.
2. Price-level container.
3. Add order.
4. Best bid/ask.
5. Match one order.
6. Partial fill.
7. Cancellation.
8. Book snapshot.
9. Deterministic simulator.

### Tests

- Empty book.
- Single order.
- Non-crossing orders.
- Exact match.
- Partial fill.
- Multi-level fill.
- FIFO at same price.
- Invalid order.
- Cancellation.

### Exit criteria

All matching tests pass with sanitizers enabled.

---

## Phase 2 — C++ Transport

### Objectives

Expose engine events through a socket.

### Deliverables

- Server.
- Connection handling.
- Framing.
- Serialization.
- Reconnection behavior.
- Graceful shutdown.

### Debug test

```bash
nc localhost <engine-port>
```

The developer should be able to observe event lines.

---

## Phase 3 — Python Analytics

### Objectives

Consume trades and calculate:

- VWAP.
- SMA.
- EMA.
- Position.
- PnL.
- Drawdown.

### Development method

Start with pure functions:

```text
calculate_vwap(...)
calculate_sma(...)
calculate_ema(...)
calculate_pnl(...)
calculate_drawdown(...)
```

Then integrate them into a streaming processor.

### Exit criteria

Hand-calculated fixtures match automated results.

---

## Phase 4 — Node Gateway

### Objectives

- Connect to analytics.
- Normalize messages.
- Expose REST.
- Expose WebSocket.
- Add health checks.
- Add structured logging.

### Exit criteria

A WebSocket test client receives live analytics events.

---

## Phase 5 — React Dashboard

### Objectives

Build:

- Header/status bar.
- Start/stop controls.
- Price chart.
- VWAP/SMA/EMA overlays.
- Order book panel.
- PnL cards.
- Risk panel.
- Event-rate indicator.

### UI performance

Do not render every raw event if the producer is faster than the browser.

Use:

- bounded arrays,
- update throttling,
- aggregation,
- memoized components.

---

## Phase 6 — Docker

### Objectives

Each service receives its own image.

Example:

```text
engine-cpp
analytics-py
gateway-node
dashboard-react
```

Compose defines:

- networks,
- environment variables,
- dependencies,
- health checks,
- restart behavior,
- volumes where required.

### Exit criteria

```bash
docker compose up --build
```

starts the complete MVP.

---

## Phase 7 — Testing and Hardening

Add:

- unit tests,
- integration tests,
- contract tests,
- end-to-end tests,
- failure tests,
- sanitizer runs,
- load tests.

---

## Phase 8 — Observability

Add:

- correlation IDs,
- event counters,
- latency measurements,
- structured logs,
- service health.

Optional:

- Prometheus.
- Grafana.
- OpenTelemetry.

---

## Phase 9 — Performance Mode

Only after profiling:

### Option A — shared memory

Use a ring buffer between processes.

### Option B — Protobuf/gRPC

Replace JSON serialization with strongly typed binary messages.

### Option C — batching

Process multiple events per transport operation.

Each optimization must be supported by benchmark data.

---

## Phase 10 — Portfolio Release

Prepare:

- architecture diagram,
- demo screenshots,
- benchmark report,
- test report,
- design trade-off document,
- README,
- short demo video.

---

## Milestone Table

| Milestone | Result |
|---|---|
| M0 | Specification complete |
| M1 | Matching engine works |
| M2 | Engine streams events |
| M3 | Analytics stream works |
| M4 | Gateway streams browser data |
| M5 | Dashboard works |
| M6 | Docker deployment works |
| M7 | Testing/hardening complete |
| M8 | Portfolio release |

---

## Definition of Done

A feature is done only when:

- code is implemented,
- tests exist,
- errors are handled,
- logs are useful,
- documentation is updated,
- build is reproducible,
- behavior is demonstrated.

---

## Recommended Git Strategy

Use focused branches:

```text
feature/engine-order-book
feature/engine-matching
feature/engine-socket
feature/python-analytics
feature/node-gateway
feature/react-dashboard
feature/docker
feature/testing
```

Use conventional commits where practical:

```text
feat(engine): implement price-time priority matching
test(engine): add partial fill scenarios
feat(analytics): add rolling VWAP
feat(gateway): add websocket event broadcast
feat(dashboard): add live price chart
chore(docker): containerize analytics service
```
