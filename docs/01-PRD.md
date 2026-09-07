# Cloud-Based Algorithmic Trading Engine
## Product Requirements Document (PRD)

**Document Version:** 1.0  
**Status:** Baseline / MVP Specification  
**Author:** Adarsh Kumar  
**System Type:** Educational trading simulation and distributed systems portfolio project

---

## 1. Purpose

The Cloud-Based Algorithmic Trading Engine is a simulated, polyglot trading platform designed to demonstrate how a high-performance event-processing system can be decomposed into specialized services.

The platform intentionally separates responsibilities across:

- **C++17** — low-latency market simulation, order-book management, and matching.
- **Python 3** — analytics, indicators, PnL, and risk calculations.
- **Node.js** — API gateway, WebSocket fan-out, authentication, and control APIs.
- **React + TypeScript** — real-time trading dashboard.
- **Docker Compose** — reproducible local orchestration.

The system is a **simulation**. It does not place real orders, connect to a broker, manage real money, or provide financial advice.

---

## 2. Product Vision

Build a small but credible trading-infrastructure laboratory in which a simulated market event travels through multiple specialized services and becomes a real-time visual result in a browser.

The final demonstration should allow a recruiter or engineer to:

1. Start the simulation.
2. Observe generated market events.
3. See orders enter and leave the order book.
4. Observe matches and partial fills.
5. Watch VWAP and moving averages update.
6. Monitor simulated positions, PnL, and risk.
7. Stop and restart the simulation.
8. Inspect service health and event statistics.
9. Run the complete stack with one Docker Compose command.

---

## 3. Goals

### 3.1 Primary goals

- Implement a correct price-time-priority limit order book.
- Demonstrate partial fills and order lifecycle management.
- Process a deterministic simulated market stream.
- Establish reliable inter-process communication.
- Demonstrate a meaningful C++/Python boundary.
- Provide real-time browser updates through WebSockets.
- Provide REST endpoints for control and historical/summary data.
- Containerize every service.
- Provide unit, integration, contract, and end-to-end testing.
- Measure throughput and basic latency.

### 3.2 Secondary goals

- Add structured logging and correlation IDs.
- Support configurable simulation speed.
- Provide configurable analytics windows.
- Demonstrate graceful startup and shutdown.
- Provide reproducible development environments.
- Document design trade-offs for interviews.

---

## 4. Non-Goals

The following are explicitly outside the scope:

- Real exchange connectivity.
- Real brokerage account integration.
- Real-money order execution.
- Investment recommendations.
- Production-grade financial compliance.
- Guaranteed high-frequency-trading performance.
- Prediction of future market prices.
- Real payment processing.
- Real user financial data.

The term "low latency" refers to the engineering objective of the simulation, not a claim that the application is comparable to a colocated exchange matching engine.

---

## 5. Target Users

### 5.1 Primary user: developer/recruiter

A technical reviewer should be able to understand the architecture and run the project locally.

### 5.2 Secondary user: system demonstrator

A developer should be able to start the system and use the dashboard to demonstrate the complete event pipeline.

### 5.3 Future user: quant/researcher

A future extension could allow a user to plug in custom analytics or strategy modules without modifying the matching engine.

---

## 6. Functional Requirements

### FR-001 — Simulation lifecycle

The system shall support:

- Start simulation.
- Stop simulation.
- Restart simulation.
- Query current simulation state.
- Configure simulation speed where supported.

States:

```text
STOPPED
STARTING
RUNNING
STOPPING
ERROR
```

### FR-002 — Market event generation

The C++ engine shall generate deterministic simulated events when a fixed seed is configured.

Events may include:

- New buy order.
- New sell order.
- Cancellation.
- Trade/fill.
- Market-data tick.
- Order-book snapshot.

### FR-003 — Order book

The engine shall maintain:

- Bid side.
- Ask side.
- Price levels.
- FIFO ordering within each price level.
- Remaining quantity.
- Order status.

### FR-004 — Matching

A buy order can execute against the best ask when:

```text
buy_price >= ask_price
```

A sell order can execute against the best bid when:

```text
sell_price <= bid_price
```

Matching shall follow price-time priority.

### FR-005 — Partial fills

If incoming quantity is greater than resting quantity, the resting order shall be fully filled and the incoming order shall continue matching.

If incoming quantity is smaller, the resting order shall remain in the book with reduced quantity.

### FR-006 — Analytics

The Python service shall calculate, at minimum:

- VWAP.
- Simple Moving Average.
- Exponential Moving Average.
- Simulated position.
- Realized PnL.
- Unrealized PnL.
- Equity.
- Drawdown.
- Basic exposure/risk ratios.

### FR-007 — WebSocket streaming

The Node gateway shall broadcast normalized analytics events to connected browser clients.

### FR-008 — REST control

The gateway shall provide APIs for:

- Health.
- Simulation status.
- Start.
- Stop.
- Configuration.
- Current metrics.
- Summary/history where implemented.

### FR-009 — Dashboard

The React application shall display:

- Connection status.
- Simulation state.
- Latest price.
- Bid/ask.
- Trade activity.
- Price chart.
- VWAP.
- Moving averages.
- Position.
- PnL.
- Drawdown.
- Event rate.
- Service health.

### FR-010 — Observability

Every service shall produce structured logs where practical.

Events should include:

- Timestamp.
- Service.
- Severity.
- Correlation/event ID.
- Event type.
- Useful context.

---

## 7. Non-Functional Requirements

### NFR-001 Performance

The C++ engine should be optimized for high event throughput while preserving correctness.

The project shall report measured throughput rather than making unsupported performance claims.

### NFR-002 Determinism

Test scenarios shall support deterministic seeds and known expected outputs.

### NFR-003 Reliability

A failure in one service shall be detectable through health checks and logs.

### NFR-004 Security

The gateway shall validate input, restrict control endpoints, and avoid exposing internal service ports unnecessarily.

### NFR-005 Maintainability

Each service shall have a clear responsibility and an independently understandable source tree.

### NFR-006 Portability

The application shall run through Docker Compose on a standard Linux development machine.

### NFR-007 Testability

Core matching and analytics algorithms shall be testable without requiring the complete distributed stack.

---

## 8. Success Criteria

The MVP is complete when:

- A deterministic order sequence produces expected fills.
- Partial fills work.
- C++ emits valid events.
- Python consumes events and computes metrics.
- Node receives and broadcasts events.
- React renders live updates.
- Start/stop controls work.
- Docker Compose starts the system.
- Automated tests pass.
- README instructions reproduce the demo.

---

## 9. Acceptance Scenarios

### Scenario A — basic match

Given:

```text
SELL 10 @ 101
BUY  10 @ 101
```

Expected:

```text
TRADE quantity = 10
price = 101
remaining sell = 0
remaining buy = 0
```

### Scenario B — partial fill

Given:

```text
SELL 100 @ 101
BUY  40 @ 101
```

Expected:

```text
TRADE quantity = 40
remaining sell = 60
remaining buy = 0
```

### Scenario C — no crossing

Given:

```text
SELL 100 @ 105
BUY  100 @ 104
```

Expected:

```text
No trade
Both orders remain in the book.
```

---

## 10. Future Extensions

Potential later phases:

- Redis Streams/PubSub.
- Protobuf/gRPC.
- Shared-memory transport.
- Strategy plugin interface.
- PostgreSQL persistence.
- Replayable event logs.
- Multiple instruments.
- Multi-account simulation.
- Load testing.
- Distributed gateway instances.
- Prometheus/Grafana observability.

---

## 11. Product Principles

1. Correctness before speed.
2. Explicit service boundaries.
3. Deterministic tests.
4. Observable behavior.
5. Measured performance.
6. Security by default.
7. Documentation as part of the implementation.
8. No claims of real trading capability.
