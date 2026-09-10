# Roadmap and Implementation Phases

## 1. Strategy

Development follows a vertical-slice approach: each phase produces something executable, testable, and reviewable.

The goal is not to build every abstraction before validating the system end-to-end.

Each phase should:

- produce working code;
- include automated tests;
- maintain documentation;
- preserve backward compatibility where applicable;
- have a clearly defined exit criterion;
- be independently reviewable.

---

# Phase 0 — Product Specification

## Status

✅ **Complete**

## Objectives

- Freeze MVP scope.
- Define event schemas.
- Define repository structure.
- Define test strategy.
- Define success criteria.
- Establish system architecture and component boundaries.

## Deliverables

```text
docs/01-product-requirements.md
docs/02-architecture.md
docs/03-data-model.md
docs/04-api-reference.md
docs/05-roadmap-and-phases.md
docs/06-testing-strategy.md
docs/07-security.md
```

## Exit Criteria

A developer can explain the complete event journey without reading implementation code.

---

# Phase 1 — C++ Order Book

## Status

✅ **Complete**

## Objectives

Implement the deterministic C++ matching core:

* Order model.
* Price-level container.
* Bid book.
* Ask book.
* Matching engine.
* Trade generation.
* Cancellation.
* Book snapshot.
* Deterministic market-data simulation.

## Implementation Order

1. Order model.
2. Price-level container.
3. Add order.
4. Best bid/ask.
5. Match one order.
6. Partial fill.
7. Cancellation.
8. Book snapshot.
9. Deterministic simulator.

## Tests

* Empty book.
* Single order.
* Non-crossing orders.
* Exact match.
* Partial fill.
* Multi-level fill.
* FIFO at same price.
* Invalid order.
* Cancellation.
* Deterministic matching behavior.

## Exit Criteria

All matching tests pass with sanitizers enabled.

## Completion Result

The C++ order-book and matching engine are implemented and tested.

The engine can:

```text
Receive Orders
      ↓
Validate Orders
      ↓
Maintain Bid/Ask Books
      ↓
Match Crossing Orders
      ↓
Generate Trades
      ↓
Publish Engine Events
```

---

# Phase 2 — C++ Transport

## Status

✅ **Complete**

## Objectives

Expose engine events through a TCP transport layer.

The transport provides a stable communication boundary between the C++ trading engine and downstream services.

## Deliverables

* TCP socket server.
* Client connection management.
* Message framing.
* JSON serialization.
* Heartbeat handling.
* Reconnection support.
* Graceful shutdown.
* Broadcast support.
* Transport-level error handling.

## Wire Protocol

The MVP transport protocol uses:

```text
4-byte unsigned payload length
        ↓
Big-endian byte order
        ↓
UTF-8 JSON payload
```

Maximum supported payload size:

```text
1 MiB
```

## Message Types

The transport supports the following message types:

```text
UNKNOWN
HELLO
HEARTBEAT
ORDER
TRADE
MARKET_DATA
BOOK_SNAPSHOT
ERROR
SHUTDOWN
```

## Runtime Configuration

Default engine transport configuration:

```text
Host: 127.0.0.1
Port: 9000
Heartbeat interval: 10 seconds
Heartbeat timeout: 30 seconds
```

## Debug Test

The transport can be inspected using a TCP client such as:

```bash
nc localhost 9000
```

## Testing

Transport testing covers:

* Frame creation.
* Frame parsing.
* JSON serialization.
* Message deserialization.
* Client connection.
* Heartbeat handling.
* Reconnection behavior.
* Graceful shutdown.
* Multiple clients.
* Broadcast behavior.

## Exit Criteria

The C++ transport successfully:

1. Starts a TCP server.
2. Accepts client connections.
3. Frames outgoing messages.
4. Serializes messages as JSON.
5. Sends engine events.
6. Handles heartbeats.
7. Detects disconnected clients.
8. Shuts down gracefully.
9. Passes automated transport tests.

## Completion Result

Phase 2 provides the network boundary required by downstream analytics and gateway services.

---

# Phase 3 — Python Analytics

## Status

🟡 **In Progress**

## Objectives

Build the Python analytics service that consumes trading-engine events and calculates analytical metrics.

The analytics service is intentionally separated from the C++ matching engine.

The C++ engine remains responsible for:

* order management;
* matching;
* trade generation;
* deterministic market simulation;
* low-latency transport.

The Python service is responsible for:

* event ingestion;
* analytical calculations;
* streaming processing;
* risk calculations;
* publishing analytics results.

---

## Phase 3.1 — Python Foundation

### Status

✅ **Complete**

### Objectives

Establish the Python analytics service foundation.

### Deliverables

* Python package structure.
* Runtime configuration.
* Logging utilities.
* Time utilities.
* Test infrastructure.
* Packaging configuration.

### Result

The analytics service has a clean Python package structure suitable for incremental development.

---

# Phase 3.2 — Domain Models

## Status

✅ **Complete**

## Objectives

Create strongly defined domain models for analytics processing.

## Models

```text
Tick
Trade
AnalyticsResult
```

## Responsibilities

### Tick

Represents market-data observations.

### Trade

Represents executed trades received from the trading engine.

### AnalyticsResult

Represents calculated analytics output.

## Testing

Domain model tests cover:

* Construction.
* Required fields.
* Default values.
* Type behavior.
* Validation.
* Serialization-related behavior where applicable.

---

# Phase 3.3 — Technical Indicators

## Status

✅ **Complete**

## Objectives

Implement deterministic analytical functions.

## Indicators

```text
SMA
EMA
VWAP
Volatility
```

## Design Principle

Indicators are implemented as deterministic functions that can be tested independently from networking and streaming infrastructure.

Example conceptual interfaces:

```text
calculate_sma(...)
calculate_ema(...)
calculate_vwap(...)
calculate_volatility(...)
```

## Testing

Tests verify:

* Hand-calculated values.
* Empty inputs.
* Small datasets.
* Boundary conditions.
* Floating-point behavior.
* Deterministic output.

## Result

The analytics layer can calculate core market indicators independently of the transport layer.

---

# Phase 3.4 — Socket Ingestion

## Status

✅ **Complete**

## Objectives

Connect the Python analytics service to the C++ engine transport.

The Python ingestion layer consumes the same framed JSON protocol implemented by the C++ transport.

## Protocol Compatibility

The Python client implements:

```text
4-byte big-endian payload length
        ↓
UTF-8 JSON payload
```

Maximum payload size:

```text
1 MiB
```

## Socket Client Capabilities

The Python `SocketClient` supports:

* TCP connection establishment.
* Connection timeout.
* Receive timeout.
* Framed message reception.
* Fragmented frame handling.
* Multiple frames in one read.
* Payload-size validation.
* UTF-8 validation.
* Message callbacks.
* Connection callbacks.
* Disconnect callbacks.
* Optional automatic reconnection.
* Graceful shutdown.
* Transport-level heartbeat handling.

## Configuration

The analytics service supports environment-based configuration:

```text
TRADING_ENGINE_HOST
TRADING_ENGINE_PORT
TRADING_ENGINE_CONNECT_TIMEOUT
TRADING_ENGINE_RECEIVE_TIMEOUT
TRADING_ENGINE_RECONNECT
TRADING_ENGINE_RECONNECT_DELAY
TRADING_ENGINE_MAX_PAYLOAD_SIZE
```

Default engine endpoint:

```text
127.0.0.1:9000
```

## Testing

Unit tests cover:

* Big-endian framing.
* Fragmented frames.
* Multiple frames in one read.
* Incomplete payload buffering.
* Oversized payload rejection.
* Invalid UTF-8 rejection.
* Heartbeat handling.
* Sending without an active connection.
* Idempotent shutdown.
* Socket-level fragmented-frame reception.

## Integration Testing

A deterministic TCP integration test verifies:

```text
TCP Server
    ↓
Framed HELLO
    ↓
Framed TRADE
    ↓
Python SocketClient
    ↓
Message Callback
    ↓
JSON Validation
```

The integration test intentionally uses a deterministic local TCP server that implements the exact C++ transport wire protocol.

## C++ ↔ Python Interoperability

Manual end-to-end interoperability was verified against the running C++ engine.

Verified behavior includes:

```text
C++ Engine
    ↓
TCP Transport
    ↓
Python SocketClient
    ↓
HELLO
TRADE
HEARTBEAT
    ↓
Python callbacks
```

Observed trade messages contain:

```text
symbol
price
quantity
taker_order_id
maker_order_id
```

Python successfully received real trade events from the C++ engine and responded to transport heartbeats.

## Test Result

The complete Python analytics test suite currently passes:

```text
66 passed
```

## Exit Criteria

Phase 3.4 is considered complete when:

* Python can connect to the C++ transport.
* Framed messages are decoded correctly.
* Fragmented TCP frames are handled.
* Multiple messages can be processed.
* Oversized payloads are rejected.
* Invalid UTF-8 is rejected.
* Heartbeats are handled.
* Connection lifecycle callbacks work.
* Graceful shutdown works.
* Deterministic integration tests pass.
* C++ ↔ Python interoperability is manually verified.

---

# Phase 3.5 — Streaming Analytics

## Status

⏳ **Pending**

## Objectives

Connect the socket-ingestion layer to the analytics processing pipeline.

The streaming pipeline should consume incoming engine events and update analytical state continuously.

## Planned Flow

```text
C++ Trading Engine
        ↓
TCP Transport
        ↓
Python SocketClient
        ↓
Message Parser
        ↓
Streaming Processor
        ↓
┌─────────────────────────────┐
│ SMA                         │
│ EMA                         │
│ VWAP                        │
│ Volatility                  │
│ Position                    │
│ PnL                         │
│ Drawdown                    │
└─────────────────────────────┘
        ↓
Analytics Result
        ↓
Publisher
```

## Planned Work

* Parse incoming trade messages.
* Convert transport messages into domain models.
* Feed trades into the streaming processor.
* Maintain indicator state.
* Maintain position state.
* Calculate PnL.
* Calculate drawdown.
* Produce `AnalyticsResult`.
* Add streaming integration tests.
* Verify deterministic output using fixtures.

## Exit Criteria

A live trade received from the C++ engine can travel through the Python analytics pipeline and produce a validated analytics result.

---

# Phase 3.6 — Risk Analytics

## Status

⏳ **Pending**

## Objectives

Add risk-management calculations to the analytics service.

## Planned Components

```text
Position Sizing
PnL
Drawdown
Risk Manager
```

## Exit Criteria

Risk calculations pass deterministic fixtures and integrate with the streaming analytics pipeline.

---

# Phase 3.7 — Analytics Publishing

## Status

⏳ **Pending**

## Objectives

Publish calculated analytics results to downstream services.

## Planned Work

* Define analytics-result event format.
* Implement publisher.
* Add output validation.
* Add integration tests.
* Prepare interface for the Node gateway.

## Exit Criteria

Analytics results can be published through a stable service interface.

---

# Phase 4 — Node Gateway

## Status

⏳ **Pending**

## Objectives

Build the Node.js gateway responsible for exposing trading-engine functionality to external clients.

## Planned Components

* HTTP API.
* WebSocket API.
* Authentication.
* Authorization.
* Request validation.
* Engine communication.
* Analytics communication.
* API error handling.

## Planned Flow

```text
Client
  ↓
Node Gateway
  ↓
C++ Engine / Python Analytics
  ↓
Response
```

## Exit Criteria

A client can interact with the trading platform through documented HTTP/WebSocket APIs.

---

# Phase 5 — Web Dashboard

## Status

⏳ **Pending**

## Objectives

Build a real-time web dashboard for monitoring the trading system.

## Planned Features

* Market data view.
* Order book.
* Recent trades.
* VWAP.
* SMA.
* EMA.
* Volatility.
* Position.
* PnL.
* Drawdown.
* Connection status.
* Engine status.
* Real-time updates.

## Exit Criteria

The dashboard displays live data received from the gateway.

---

# Phase 6 — Persistence

## Status

⏳ **Pending**

## Objectives

Introduce persistent storage for trading and analytics data.

## Planned Data

* Orders.
* Trades.
* Market data.
* Positions.
* Analytics results.
* System events.

## Planned Work

* Database schema.
* Repository layer.
* Persistence service.
* Historical queries.
* Retention policy.
* Backup strategy.

## Exit Criteria

Trading and analytics data can be persisted and retrieved reliably.

---

# Phase 7 — Authentication and Security

## Status

⏳ **Pending**

## Objectives

Secure external APIs and internal service communication.

## Planned Features

* Authentication.
* Authorization.
* Token management.
* Role-based access.
* Input validation.
* Rate limiting.
* Audit logging.
* Secret management.
* Secure configuration.

## Exit Criteria

Unauthorized users cannot access protected trading operations.

---

# Phase 8 — Observability

## Status

⏳ **Pending**

## Objectives

Make the distributed system observable.

## Planned Components

* Structured logging.
* Metrics.
* Health checks.
* Readiness checks.
* Liveness checks.
* Distributed tracing.
* Performance monitoring.
* Error tracking.

## Planned Metrics

```text
Orders/sec
Trades/sec
Matching latency
Transport latency
Socket connections
Message throughput
Analytics processing latency
API latency
Error rate
CPU usage
Memory usage
```

## Exit Criteria

Operators can identify system health, performance bottlenecks, and failures.

---

# Phase 9 — Deployment

## Status

⏳ **Pending**

## Objectives

Prepare the platform for reproducible deployment.

## Planned Work

* Docker images.
* Docker Compose environment.
* Environment configuration.
* Service networking.
* Health checks.
* Deployment documentation.
* Operational runbook.

## Target Services

```text
C++ Trading Engine
Python Analytics
Node Gateway
Web Dashboard
Database
Observability Stack
```

## Exit Criteria

The complete platform can be started using a documented deployment procedure.

---

# Phase 10 — Performance and Production Hardening

## Status

⏳ **Pending**

## Objectives

Validate system performance and prepare the platform for production-like workloads.

## Planned Work

* Load testing.
* Stress testing.
* Latency benchmarking.
* Memory profiling.
* CPU profiling.
* Concurrency testing.
* Failure injection.
* Recovery testing.
* Security review.
* Performance regression tests.

## Performance Areas

### Matching Engine

Measure:

```text
Orders/sec
Trades/sec
Matching latency
p50 latency
p95 latency
p99 latency
```

### Transport

Measure:

```text
Messages/sec
Connection latency
Serialization latency
End-to-end latency
```

### Analytics

Measure:

```text
Events/sec
Processing latency
Indicator calculation cost
Memory growth
```

## Exit Criteria

The platform meets documented MVP performance and reliability targets.

---

# Milestone Summary

| Phase     | Component                 | Status     |
| --------- | ------------------------- | ---------- |
| Phase 0   | Product Specification     | ✅ Complete |
| Phase 1   | C++ Order Book            | ✅ Complete |
| Phase 2   | C++ Transport             | ✅ Complete |
| Phase 3.1 | Python Foundation         | ✅ Complete |
| Phase 3.2 | Domain Models             | ✅ Complete |
| Phase 3.3 | Technical Indicators      | ✅ Complete |
| Phase 3.4 | Socket Ingestion          | ✅ Complete |
| Phase 3.5 | Streaming Analytics       | ⏳ Pending  |
| Phase 3.6 | Risk Analytics            | ⏳ Pending  |
| Phase 3.7 | Analytics Publishing      | ⏳ Pending  |
| Phase 4   | Node Gateway              | ⏳ Pending  |
| Phase 5   | Web Dashboard             | ⏳ Pending  |
| Phase 6   | Persistence               | ⏳ Pending  |
| Phase 7   | Authentication & Security | ⏳ Pending  |
| Phase 8   | Observability              | ⏳ Pending  |
| Phase 9   | Deployment                | ⏳ Pending  |
| Phase 10  | Performance & Hardening   | ⏳ Pending  |

---

# Recommended Development Order

The recommended implementation sequence is:

```text
Phase 0
   ↓
Phase 1
   ↓
Phase 2
   ↓
Phase 3.1
   ↓
Phase 3.2
   ↓
Phase 3.3
   ↓
Phase 3.4
   ↓
Phase 3.5
   ↓
Phase 3.6
   ↓
Phase 3.7
   ↓
Phase 4
   ↓
Phase 5
   ↓
Phase 6
   ↓
Phase 7
   ↓
Phase 8
   ↓
Phase 9
   ↓
Phase 10
```

The next implementation target is:

```text
Phase 3.5 — Streaming Analytics
```

---

# Vertical-Slice Validation

Each major phase should be validated through an executable end-to-end path.

## Current Validated Slice

The project currently supports:

```text
C++ Order
    ↓
Order Book
    ↓
Matching Engine
    ↓
Trade Generation
    ↓
C++ TCP Transport
    ↓
Framed JSON Message
    ↓
Python SocketClient
    ↓
Python Callback
```

This represents the current Phase 1 → Phase 2 → Phase 3.4 vertical slice.

## Next Vertical Slice

Phase 3.5 will extend the flow to:

```text
C++ Order
    ↓
Order Book
    ↓
Matching Engine
    ↓
Trade
    ↓
C++ Transport
    ↓
Python SocketClient
    ↓
Message Parser
    ↓
Streaming Processor
    ↓
Indicators / Position / PnL / Risk
    ↓
AnalyticsResult
```

---

# Testing Strategy Across Phases

Every implementation phase should contain appropriate testing at multiple levels.

## Unit Tests

Test individual functions and classes in isolation.

## Integration Tests

Test communication between modules and services.

## End-to-End Tests

Test complete system flows.

## Deterministic Tests

Use fixed inputs and expected outputs wherever possible.

## Performance Tests

Measure throughput and latency for performance-sensitive components.

## Sanitizer Testing

C++ components should be validated with appropriate sanitizers during development.

---

# Git Branch Strategy

Development should use feature branches for each major implementation phase.

Example:

```text
main
 │
 ├── feature/phase1-order-book
 │
 ├── feature/phase2-cpp-transport
 │
 ├── feature/phase3-python-foundation
 │
 ├── feature/phase3.2-domain-models
 │
 ├── feature/phase3.3-indicators
 │
 ├── feature/phase3.4-socket-ingestion
 │
 └── feature/phase3.5-streaming-analytics
```

Completed work should be reviewed and merged into `main`.

The `main` branch should remain buildable and testable.

---

# Definition of Done

A phase is considered complete only when:

* Implementation is complete.
* Unit tests are present.
* Integration tests are added where applicable.
* Existing tests continue to pass.
* Documentation is updated.
* Error handling is implemented.
* Configuration is documented.
* Relevant performance considerations are recorded.
* `git diff --check` passes.
* The feature branch is ready for review.
* The implementation is merged into `main`.

---

# Current Project Status

As of September 10, 2026:

```text
Phase 0        ████████████████████ 100%  Complete
Phase 1        ████████████████████ 100%  Complete
Phase 2        ████████████████████ 100%  Complete
Phase 3.1      ████████████████████ 100%  Complete
Phase 3.2      ████████████████████ 100%  Complete
Phase 3.3      ████████████████████ 100%  Complete
Phase 3.4      ████████████████████ 100%  Complete
Phase 3.5      ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 3.6      ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 3.7      ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 4        ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 5        ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 6        ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 7        ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 8        ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 9        ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 10       ░░░░░░░░░░░░░░░░░░░░   0%  Pending
```

The project has completed the C++ matching-engine foundation, C++ transport layer, and the first four Python analytics stages.

The immediate next milestone is:

```text
Phase 3.5 — Streaming Analytics
```