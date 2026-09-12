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
taker_side
buy_order_id
sell_order_id
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

✅ **Complete**

## Objectives

Connect the socket-ingestion layer to the analytics processing pipeline.

The streaming pipeline consumes incoming trading-engine events, converts them into domain models, updates per-symbol analytical state, produces deterministic analytics results, and publishes those results through a transport-independent publisher interface.

## Implemented Flow

```text
C++ Trading Engine
        ↓
TCP Transport
        ↓
Python SocketClient
        ↓
Message Parser
        ↓
Trade Domain Model
        ↓
StreamingProcessor
        ↓
┌─────────────────────────────┐
│ SMA                         │
│ EMA                         │
│ VWAP                        │
│ Volatility                  │
└─────────────────────────────┘
        ↓
AnalyticsResult
        ↓
AnalyticsPublisher
        ↓
JSON Output / Injected Sink
```

## Implemented Components

### Streaming Processor

The streaming processor:

* consumes parsed trade events;
* maintains per-symbol streaming state;
* updates indicators incrementally;
* preserves source event timestamps;
* produces deterministic `AnalyticsResult` objects;
* supports repeated processing of events for the same symbol.

### Indicator State

Streaming state currently supports:

```text
SMA
EMA
VWAP
Volatility
```

Indicator calculations are updated as new trade events arrive rather than requiring the complete historical dataset to be recalculated.

### Analytics Result

Each processed trade produces an `AnalyticsResult` containing the current analytical state for the symbol.

The result includes:

```text
event_id
event_type
timestamp
symbol
price
quantity
vwap
sma
ema
volatility
position
realized_pnl
unrealized_pnl
equity
peak_equity
drawdown
```

The risk and position-related fields are currently retained as deterministic zero/default values until explicit trade-side information is available from the engine protocol.

### Analytics Publisher

A transport-independent `AnalyticsPublisher` was implemented to separate analytics calculation from downstream delivery.

The publisher supports:

* injected callable sinks;
* deterministic JSON serialization;
* compact output;
* stable key ordering;
* unique analytics event identifiers;
* publication without coupling the analytics processor to a specific transport.

Example output type:

```text
ANALYTICS_UPDATE
```

### Service Integration

The `AnalyticsService` now orchestrates:

```text
SocketClient
    ↓
Incoming Message
    ↓
Trade Parsing
    ↓
StreamingProcessor
    ↓
AnalyticsResult
    ↓
AnalyticsPublisher
```

The service can therefore process a live engine event through the complete Phase 3.5 pipeline.

## Protocol Compatibility

Phase 3.5 consumes the existing C++ `TRADE` message schema without modifying the transport protocol.

Current trade fields are:

```text
symbol
price
quantity
taker_order_id
maker_order_id
```

The existing protocol does not expose a reliable explicit BUY/SELL side for the executed trade.

Therefore Phase 3.5 intentionally does not attempt to infer trading position direction from order identifiers.

Position, PnL, equity, and drawdown calculations are implemented in Phase 3.6 using the reliable trade-side information now exposed by the TRADE protocol.

## End-to-End Validation

A deterministic end-to-end test verifies:

```text
Raw TRADE JSON
      ↓
Message Parser
      ↓
Trade
      ↓
StreamingProcessor
      ↓
AnalyticsResult
      ↓
AnalyticsPublisher
      ↓
Deterministic JSON Sink
```

The pipeline has also been manually verified using a C++-compatible `TRADE` payload.

## Testing

Phase 3.5 validation includes:

* streaming processor unit tests;
* publisher unit tests;
* analytics-service integration tests;
* deterministic serialization tests;
* end-to-end raw-message processing;
* existing Phase 3 regression tests.

Current complete Python test suite:

```text
92 passed
```

Targeted publisher tests:

```text
6 passed
```

## Deferred Work

The following functionality is intentionally deferred:

```text
Position tracking
Realized PnL
Unrealized PnL
Equity
Peak equity
Drawdown
Risk calculations
```

These belong to Phase 3.6 and require reliable trade-side information from the trading-engine protocol.

## Exit Criteria

Phase 3.5 is complete because:

* incoming trade messages can be parsed;
* trades are converted into domain models;
* streaming state is maintained per symbol;
* indicators are updated incrementally;
* `AnalyticsResult` objects are produced;
* analytics results have deterministic event identifiers;
* analytics results can be published;
* output serialization is deterministic;
* end-to-end pipeline processing is verified;
* the complete Python test suite passes.

## Completion Result

Phase 3.5 establishes the first complete Python streaming analytics slice:

```text
C++ Trade
    ↓
TCP Transport
    ↓
Python SocketClient
    ↓
Trade Parser
    ↓
StreamingProcessor
    ↓
Indicators
    ↓
AnalyticsResult
    ↓
AnalyticsPublisher
```

The analytics service is now capable of processing engine-generated trade events continuously and producing downstream-consumable analytics events.

---

# Phase 3.6 — Risk Analytics

## Status

✅ **Complete**

## Objectives

Add position and risk-management calculations to the streaming analytics service.

Phase 3.6 extends the Phase 3.5 streaming pipeline with trade-direction-aware portfolio state, including position tracking, realized and unrealized PnL, equity, peak equity, drawdown, and immutable risk snapshots.

## Implemented Components

- Trade-side-aware position tracking
- Realized PnL calculation
- Unrealized PnL calculation
- Equity tracking
- Peak-equity tracking
- Drawdown calculation
- `RiskManager`
- Immutable `RiskSnapshot`
- Per-symbol risk state
- Integration with `StreamingProcessor`
- Risk fields propagated into `AnalyticsResult`
- Public risk-module exports
- Unit and integration test coverage

## Trade-Side Protocol

The C++ `TRADE` event provides reliable trade-direction information through:

```text
taker_side
buy_order_id
sell_order_id
```

The Python message parser validates taker_side and propagates the direction into the Trade domain model.

This provides deterministic BUY/SELL information for downstream position and PnL calculations.

Position Tracking

The risk subsystem maintains independent position state for each symbol.

Supported position transitions include:

```text
Flat → Long
Flat → Short
Long → Long
Short → Short
Long → Flat
Short → Flat
Long → Short
Short → Long
```

Average entry price is maintained for open positions.

### Realized PnL

For long positions:

```text
realized PnL = (exit price - entry price) × quantity
```

For short positions:

```text
realized PnL = (entry price - exit price) × quantity
```

### Unrealized PnL

Unrealized PnL is calculated from the current market price, open position, and average entry price.

Equity

```text
equity = initial equity + realized PnL + unrealized PnL
```

Peak Equity

Peak equity tracks the highest observed equity value.

Drawdown

```text
drawdown = peak equity - current equity
```

### RiskManager

RiskManager maintains mutable risk state and returns immutable RiskSnapshot objects.

The snapshot contains:

```text
position
average_entry_price
realized_pnl
unrealized_pnl
equity
peak_equity
drawdown
```

### Streaming Integration

StreamingProcessor maintains a RiskManager for each symbol and uses the parsed taker_side to update risk state.

Each AnalyticsResult now contains:

```text
position
realized_pnl
unrealized_pnl
equity
peak_equity
drawdown
```

alongside the existing technical indicators.

### Risk Module

The Phase 3.6 risk package provides:

```text
analytics.risk.pnl
analytics.risk.drawdown
analytics.risk.position_sizing
analytics.risk.risk_manager
```

The public API exposes:

```text
calculate_realized_pnl(...)
calculate_unrealized_pnl(...)
calculate_drawdown(...)
update_peak_equity(...)
calculate_position_value(...)
update_position(...)
```

and:

```text
RiskManager
RiskSnapshot
```

## Testing

Phase 3.6 validation includes:

- Realized PnL tests
- Unrealized PnL tests
- Drawdown tests
- Peak-equity tests
- Position update tests
- Position sizing tests
- RiskManager tests
- Streaming processor risk integration tests
- Trade-side parser regression tests
- Full Python regression suite

Current complete Python test suite:

```text
144 passed
```

## Exit Criteria

Phase 3.6 is complete because:

- Reliable trade-side information is available from the C++ TRADE protocol.
- Python validates and propagates trade direction.
- Position state is maintained per symbol.
- Realized PnL is calculated deterministically.
- Unrealized PnL is calculated deterministically.
- Equity is tracked.
- Peak equity is tracked.
- Drawdown is calculated.
- Risk snapshots are produced.
- Risk state is integrated into AnalyticsResult.
- Regression tests pass.

## Completion Result

Phase 3.6 completes the risk-aware streaming analytics slice:

```text
C++ Trade + Side
       ↓
C++ TCP Transport
       ↓
Python SocketClient
       ↓
Message Parser
       ↓
Trade Domain Model
       ↓
StreamingProcessor
       ↓
Indicators + RiskManager
       ↓
Position / PnL / Equity / Drawdown
       ↓
AnalyticsResult
       ↓
AnalyticsPublisher
```

---

# Phase 3.7 — Analytics Publishing

## Status

⏳ **Pending**

## Objectives

Harden analytics-result publication for downstream services.

Phase 3.5 already provides the initial transport-independent publisher implementation. Phase 3.7 will formalize the downstream publishing contract and prepare it for integration with the Node gateway.

## Planned Work

* Freeze the analytics-result event schema.
* Define downstream event contracts.
* Add output validation.
* Add publisher reliability handling.
* Add integration tests.
* Prepare gateway integration.
* Document analytics event compatibility.
* Define delivery and failure semantics.

## Exit Criteria

Analytics results can be published through a documented and stable service interface suitable for consumption by the Node gateway.

---

# Phase 4 — Node Gateway

## Status

✅ **Complete**

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

✅ **Complete**

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

✅ **Complete**

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

✅ **Complete**

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

✅ **Complete**

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

✅ **Complete**

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

✅ **Complete**

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

| Phase     | Component                 | Status      |
| --------- | ------------------------- | ----------- |
| Phase 0   | Product Specification     | ✅ Complete |
| Phase 1   | C++ Order Book            | ✅ Complete |
| Phase 2   | C++ Transport             | ✅ Complete |
| Phase 3.1 | Python Foundation         | ✅ Complete |
| Phase 3.2 | Domain Models             | ✅ Complete |
| Phase 3.3 | Technical Indicators      | ✅ Complete |
| Phase 3.4 | Socket Ingestion          | ✅ Complete |
| Phase 3.5 | Streaming Analytics       | ✅ Complete |
| Phase 3.6 | Risk Analytics            | ✅ Complete |
| Phase 3.7 | Analytics Publishing      | ⏳ Pending  |
| Phase 4   | Node Gateway              | ⏳ Pending  |
| Phase 5   | Web Dashboard             | ⏳ Pending  |
| Phase 6   | Persistence               | ⏳ Pending  |
| Phase 7   | Authentication & Security | ⏳ Pending  |
| Phase 8   | Observability             | ⏳ Pending  |
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
Message Parser
    ↓
Trade Domain Model
    ↓
StreamingProcessor
    ↓
Indicator State
    ↓
AnalyticsResult
    ↓
AnalyticsPublisher
    ↓
Deterministic JSON Output
```

This represents the completed:

```text
Phase 1 → Phase 2 → Phase 3.1 → Phase 3.2 → Phase 3.3 → Phase 3.4 → Phase 3.5
```

vertical slice.

## Next Vertical Slice

Phase 3.6 extends the flow with trade-side-aware risk analytics:

```text
C++ Order
    ↓
Order Book
    ↓
Matching Engine
    ↓
Trade + Side
    ↓
C++ Transport
    ↓
Python SocketClient
    ↓
Message Parser
    ↓
StreamingProcessor
    ↓
Indicators
    ↓
Position
    ↓
PnL
    ↓
Equity / Drawdown
    ↓
Risk Analytics
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

As of **September 12, 2026**:

```text
Phase 0        ████████████████████ 100%  Complete
Phase 1        ████████████████████ 100%  Complete
Phase 2        ████████████████████ 100%  Complete
Phase 3.1      ████████████████████ 100%  Complete
Phase 3.2      ████████████████████ 100%  Complete
Phase 3.3      ████████████████████ 100%  Complete
Phase 3.4      ████████████████████ 100%  Complete
Phase 3.5      ████████████████████ 100%  Complete
Phase 3.6      ████████████████████ 100%  Complete
Phase 3.7      ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 4        ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 5        ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 6        ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 7        ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 8        ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 9        ░░░░░░░░░░░░░░░░░░░░   0%  Pending
Phase 10       ░░░░░░░░░░░░░░░░░░░░   0%  Pending
```

The project has completed:

* C++ matching-engine foundation.
* C++ TCP transport layer.
* Python analytics foundation.
* Python domain models.
* Technical indicators.
* Python socket ingestion.
* Streaming analytics processing.
* Analytics-result generation.
* Analytics-result publishing.

The current Python analytics test suite passes:

```text
92 passed
```

The immediate next milestone is:

```text
Phase 3.6 — Risk Analytics
```

Phase 3.6 will introduce trade-direction-aware position, PnL, equity, drawdown, and risk calculations after the trade protocol is extended with reliable side information.
