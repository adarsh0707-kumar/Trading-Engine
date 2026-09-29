# Trading Engine — Roadmap & Phases

This roadmap tracks the implementation state of the **Cloud-Based Algorithmic Trading Engine**.

The project is developed incrementally across the C++ matching engine, TCP transport, Python analytics, PostgreSQL persistence, observability, gateway, dashboard, infrastructure, security, and production hardening layers.

## Status Legend

- ✅ Complete
- 🚧 In Progress
- ⏳ Planned
- ❌ Blocked

---

# Current Project Status

**Overall Status:** 🚧 In Progress

**Latest Completed Milestone:** Phase 3.10 — Analytics Service Hardening

**Next Milestone:** Phase 4 — Node.js Gateway

### Current validated path

```text
C++ Matching Engine
        ↓
C++ TCP Transport
        ↓
Python SocketClient
        ↓
Message Parser
        ↓
StreamingProcessor
   ├── Indicators
   └── Risk
        ↓
ProcessedTrade
        ↓
PostgreSQL Persistence
        ↓
AnalyticsPublisher
```

---

# Phase 1 — C++ Order Book & Matching Engine

**Status:** ✅ Complete

Implemented:

- Order model and validation
- Order book and price levels
- Best bid / best ask
- Matching engine
- Partial fills
- Trade generation
- Order cancellation
- Deterministic matching behavior
- Unit and integration tests
- Sanitizer validation

---

# Phase 2 — C++ TCP Transport

**Status:** ✅ Complete

Implemented:

- TCP server and client connections
- Client lifecycle management
- Length-prefixed message framing
- UTF-8 JSON payload handling
- Trade-event broadcasting
- Heartbeat / liveness
- Connection timeout handling
- Reconnection support
- Graceful shutdown
- Debug and Release test coverage
- Cross-platform CI handling

---

# Phase 3 — Python Analytics Service

**Status:** ✅ Complete

Phase 3 is complete. The Python analytics service now provides streaming analytics, portfolio risk analytics, PostgreSQL persistence, service-wide observability, and production-oriented hardening.

## Phase 3.1 — Analytics Foundation

**Status:** ✅ Complete

- Python package structure
- Configuration
- Test infrastructure
- Service foundation

## Phase 3.2 — Domain Models

**Status:** ✅ Complete

- Trade model
- AnalyticsResult model
- Typed validation
- Decimal monetary values
- Timestamp and event identity handling

## Phase 3.3 — Technical Indicators

**Status:** ✅ Complete

- VWAP
- SMA
- EMA
- Volatility
- Streaming-compatible calculations
- Edge-case and reset handling

## Phase 3.4 — Socket Ingestion

**Status:** ✅ Complete

- Python SocketClient
- C++-compatible framing
- Fragmented and multiple-frame handling
- UTF-8 and payload validation
- Reconnection
- Heartbeat handling
- Graceful shutdown
- C++ ↔ Python interoperability

## Phase 3.5 — Streaming Analytics

**Status:** ✅ Complete

- Per-symbol streaming state
- Incremental indicators
- Deterministic AnalyticsResult generation
- AnalyticsPublisher
- Stable JSON serialization
- AnalyticsService orchestration
- End-to-end TRADE → analytics-result flow

## Phase 3.6 — Risk Analytics

**Status:** ✅ Complete

- Position tracking
- Average entry price
- Realized P&L
- Unrealized P&L
- Equity and peak equity
- Drawdown
- RiskManager
- RiskSnapshot
- Per-symbol risk state
- Processor-level risk integration

## Phase 3.7 — Risk Limits and Risk Events

**Status:** ✅ Complete

Implemented risk-limit configuration, risk evaluation, warning/breach states, immutable risk events, event generation, and streaming-processor integration.

---

## Phase 3.8 — PostgreSQL Persistence & Observability

**Status:** ✅ Complete

Implemented PostgreSQL connection management, repositories, transaction boundaries, persistence failure handling, health checks, migrations, and persistence observability.

---

## Phase 3.9 — Metrics and Observability

**Status:** ✅ Complete

Implemented:

* Analytics service metrics.
* Processing-duration and latency metrics.
* Trade throughput metrics.
* Risk and risk-event metrics.
* Error counters.
* Prometheus exposition.
* Grafana dashboard provisioning.
* Service liveness/readiness metrics.
* Trading-engine connection health.
* Inbound message metrics.
* Service-health test coverage.

---

## Phase 3.10 — Analytics Service Hardening

**Status:** ✅ Complete

Implemented:

* Service lifecycle hardening.
* Configuration validation.
* Resource cleanup.
* Bounded backpressure handling.
* Failure recovery and bounded retries.
* Engine disconnect/reconnect recovery.
* Operational logging configuration.
* Standardized service, socket, parser, persistence, publisher, and processing logs.
* Recovery and operational-logging test coverage.

### Phase 3.10 Breakdown

| Sub-phase | Area | Status |
| --- | --- | --- |
| 3.10.1 | Service lifecycle hardening | ✅ Complete |
| 3.10.2 | Configuration validation | ✅ Complete |
| 3.10.3 | Resource cleanup | ✅ Complete |
| 3.10.4 | Backpressure handling | ✅ Complete |
| 3.10.5 | Failure recovery | ✅ Complete |
| 3.10.6 | Operational logging | ✅ Complete |

### Phase 3 Validation

```text
Analytics Python test suite    PASS — 447 passed
GitHub Actions checks           PASS — 9/9
```

**Phase 3.10 exit status:** ✅ Complete

---

# Phase 4 — Node.js Gateway

**Status:** ⏳ Planned

Phase 4 builds the browser-facing application gateway between the completed C++/Python platform and the future React dashboard.

## Phase 4 Technology Contract

| Area | Decision |
| --- | --- |
| Language | TypeScript |
| Runtime | Bun |
| Package manager | Bun |
| HTTP framework | Fastify |
| WebSocket transport | ws |
| Validation | Zod |
| Testing | Bun test |
| Logging | Pino |
| Metrics | Prometheus-compatible metrics |
| Configuration | Typed environment configuration |
| Upstream engine transport | TCP client using the existing engine protocol |
| External client transport | REST + WebSocket |
| Wire format | Existing JSON contracts / schemas |

Bun is the standard development and execution environment for gateway-node. npm is not the default package manager for Phase 4.

## Phase 4.1 — Gateway Foundation & Architecture

**Status:** ⏳ Planned

Establish the gateway as an independently runnable TypeScript service.

Scope:

- Initialize the gateway-node Bun/TypeScript project.
- Define a clear source/test directory structure.
- Configure strict TypeScript compilation.
- Add Bun project scripts.
- Establish application bootstrap and graceful shutdown.
- Separate transport, application services, configuration, and domain contracts.
- Define dependency boundaries so routes do not directly own upstream socket logic.
- Add a gateway health endpoint.
- Add baseline unit-test infrastructure.

Exit criteria:

- Gateway starts and stops cleanly.
- Configuration is loaded through one typed boundary.
- Health endpoint responds successfully.
- A minimal Bun test suite passes.
- No route directly manages low-level engine connection state.

## Phase 4.2 — Configuration & Environment Management

**Status:** ⏳ Planned

Define and validate all gateway runtime configuration.

Scope:

- Gateway host and port.
- C++ engine host and port.
- Analytics service connection settings.
- WebSocket path.
- Request/body size limits.
- Connection and request timeouts.
- Reconnection parameters.
- Logging level and format.
- Metrics endpoint configuration.
- CORS configuration.
- Environment-specific defaults.

Requirements:

- Fail fast on invalid required configuration.
- Never silently use malformed ports, durations, URLs, or limits.
- Keep secrets outside source control.
- Provide a complete .env.example.
- Make configuration injectable for tests.

Exit criteria:

- Valid configuration produces a runnable gateway.
- Invalid configuration fails deterministically with actionable errors.
- Configuration tests cover defaults, overrides, and invalid values.

## Phase 4.3 — C++ Engine TCP Client

**Status:** ⏳ Planned

Connect the gateway to the completed C++ trading engine without duplicating matching-engine logic.

Scope:

- Implement an asynchronous TCP client.
- Reuse the existing engine framing and JSON protocol.
- Support connection establishment and graceful disconnect.
- Handle fragmented and multiple messages.
- Validate message size before allocation/processing.
- Track engine connection state.
- Detect socket errors and remote disconnects.
- Implement bounded reconnect with backoff.
- Prevent duplicate active connections.
- Expose connection state to the gateway application layer.

The gateway must treat the C++ engine as the authoritative source for engine/order/trade state.

Exit criteria:

- Gateway can connect to a running engine.
- Valid engine events are decoded correctly.
- Fragmented frames are handled safely.
- Disconnect/reconnect behavior is deterministic.
- Socket failures do not crash the gateway.

## Phase 4.4 — Engine Protocol & Event Normalization

**Status:** ⏳ Planned

Create a stable gateway-facing event model around upstream engine messages.

Scope:

- Define typed TypeScript representations for supported engine messages.
- Validate incoming JSON against the expected schema.
- Normalize engine events into gateway domain events.
- Preserve event IDs, timestamps, symbols, quantities, prices, and order/trade identity.
- Reject malformed or unsupported event types safely.
- Prevent untrusted upstream fields from leaking into arbitrary API responses.
- Define consistent serialization for REST and WebSocket consumers.

Supported event categories should include, as applicable to the existing contracts:

text
engine_status
market_tick
order
order_book
trade
error
heartbeat

Exit criteria:

- All gateway-consumed upstream events have explicit types.
- Invalid messages are rejected and logged.
- Event identity remains traceable across services.
- REST and WebSocket payloads use documented contracts.

## Phase 4.5 — REST API

**Status:** ⏳ Planned

Expose controlled HTTP APIs for browser clients and operational tooling.

Initial API surface:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | /api/health | Gateway health |
| GET | /api/ready | Gateway readiness |
| GET | /api/status | Engine/analytics connection status |
| GET | /api/market | Current market state |
| GET | /api/orderbook | Current order-book snapshot |
| GET | /api/trades | Recent trades |
| GET | /api/analytics | Latest analytics state |
| POST | /api/engine/start | Simulation control |
| POST | /api/engine/stop | Simulation control |
| POST | /api/engine/reset | Simulation reset |

Scope:

- Route registration and versioning boundary.
- Request/response schemas.
- Parameter validation.
- Consistent HTTP status codes.
- Error response format.
- Request size/time limits.
- Upstream timeout handling.
- No direct database access from route handlers unless explicitly justified by the architecture.
- Health/readiness endpoints must remain lightweight.

Historical query endpoints are deferred to Phase 6 unless Phase 4 implementation requires a minimal read-through contract.

Exit criteria:

- Every implemented endpoint has schema validation and tests.
- Upstream failures become deterministic API errors.
- API responses are stable and documented.
- Health/readiness behavior reflects actual gateway dependencies.

## Phase 4.6 — WebSocket Gateway

**Status:** ⏳ Planned

Provide real-time browser streaming without exposing internal services directly.

Scope:

- WebSocket endpoint at the configured path.
- Connection lifecycle management.
- Client identification and subscription state.
- Typed event serialization.
- Subscription/unsubscription protocol.
- Broadcast of trade, market, order-book, analytics, and engine-status updates.
- Heartbeat/ping-pong handling.
- Dead-client cleanup.
- Per-client queue/backpressure limits.
- Slow-consumer protection.
- Graceful shutdown of active sockets.
- Avoid broadcasting duplicate events.

Initial subscription model:

text
connect
  ↓
subscribe
  ↓
event stream
  ↓
unsubscribe / disconnect

Critical trade/engine events must not be silently dropped. High-frequency display-only updates may use an explicit coalescing/drop policy when necessary.

Exit criteria:

- Multiple clients can connect concurrently.
- Clients receive only subscribed event types.
- Slow clients cannot block the gateway.
- Disconnects are cleaned up deterministically.
- WebSocket tests cover lifecycle, broadcast, invalid messages, and backpressure.

## Phase 4.7 — Python Analytics Integration

**Status:** ⏳ Planned

Integrate the completed analytics service as an upstream consumer/provider without duplicating analytics calculations.

Scope:

- Define the gateway-to-analytics integration boundary.
- Consume the existing analytics output/event contract.
- Track analytics service availability.
- Forward analytics updates to subscribed WebSocket clients.
- Expose the latest analytics snapshot through REST.
- Handle analytics disconnects and reconnects.
- Distinguish engine health from analytics health.
- Preserve event IDs and timestamps across the gateway.

The gateway is not responsible for calculating VWAP, SMA, EMA, PnL, exposure, drawdown, or risk events. Those remain owned by Python Analytics.

Exit criteria:

- Gateway can receive analytics updates.
- Analytics failures do not crash the gateway.
- Latest valid analytics state can be queried.
- Analytics events can be streamed to subscribed clients.

## Phase 4.8 — Error Handling, Resilience & Backpressure

**Status:** ⏳ Planned

Apply the reliability principles established in Phase 3 to the gateway boundary.

Scope:

- Typed application errors.
- Consistent REST error responses.
- WebSocket error events.
- Upstream connection state machines.
- Bounded reconnect attempts/backoff.
- Request timeouts.
- WebSocket send-queue limits.
- Slow-client handling.
- Malformed-message isolation.
- Graceful shutdown.
- Resource cleanup.
- Prevention of unhandled promise rejections.
- Prevention of process crashes caused by one client or one upstream failure.

Exit criteria:

- One bad request cannot crash the process.
- One malformed upstream event cannot terminate streaming.
- One slow WebSocket client cannot block other clients.
- Upstream recovery is bounded and observable.
- Shutdown releases sockets, timers, queues, and server resources.

## Phase 4.9 — Security Boundaries & Input Hardening

**Status:** ⏳ Planned

Phase 4 establishes the gateway security boundary; full authentication/authorization remains Phase 7.

Scope:

- Strict request validation.
- Maximum request/body/message sizes.
- Safe WebSocket message parsing.
- CORS policy configuration.
- Security response headers where applicable.
- Rate-limiting hooks.
- Avoid sensitive values in logs.
- Safe error messages that do not expose internal stack traces.
- Dependency/security checks.
- Authentication middleware interface prepared for Phase 7.
- Authorization middleware interface prepared for Phase 7.

No real authentication system is required to complete Phase 4 unless an implementation dependency makes a minimal mechanism necessary.

Exit criteria:

- External input is validated before application processing.
- Oversized or malformed requests are rejected safely.
- Security middleware boundaries are explicit.
- Phase 7 can add authentication without redesigning every route.

## Phase 4.10 — Operational Logging & Metrics

**Status:** ⏳ Planned

Extend the operational standards established by Python Phase 3.10 to the gateway.

Logging should cover:

text
gateway_start
gateway_stop
engine_connect_attempt
engine_connected
engine_disconnected
engine_reconnect
analytics_connected
analytics_disconnected
http_request
http_error
websocket_connected
websocket_disconnected
websocket_subscription
websocket_backpressure
upstream_message_rejected
gateway_error

Requirements:

- Structured, machine-readable fields.
- Configurable log level.
- No secrets or sensitive payloads in logs.
- Stable event names.
- Correlation/event IDs where available.

Metrics should cover at minimum:

text
HTTP request count
HTTP request latency
HTTP error count
WebSocket active connections
WebSocket messages sent
WebSocket send failures
Engine connection state
Engine reconnect count
Analytics connection state
Upstream messages received
Malformed messages
Backpressure events

Exit criteria:

- Logs are useful for tracing gateway behavior.
- Metrics are exposed through a documented endpoint.
- Gateway health and dependency state are observable.

## Phase 4.11 — Testing & Integration Validation

**Status:** ⏳ Planned

Testing must be built alongside each gateway capability.

### Unit tests

Cover:

- Configuration validation.
- Event schemas.
- Protocol parsing.
- Event normalization.
- Service logic.
- REST handlers.
- WebSocket subscription state.
- Error mapping.
- Backpressure policies.

### Integration tests

Cover:

- Gateway ↔ C++ engine TCP communication.
- Gateway ↔ analytics integration.
- REST ↔ upstream services.
- WebSocket ↔ event stream.
- Reconnect and failure recovery.
- Graceful shutdown.

### End-to-end validation

Target flow:

text
C++ Engine
    ↓
Trade Event
    ↓
Python Analytics
    ↓
Node.js Gateway
    ├── REST
    └── WebSocket
          ↓
    Future React Dashboard

Exit criteria:

- Gateway unit and integration suites pass.
- Protocol edge cases are covered.
- Failure/reconnect paths are tested.
- No known unhandled runtime errors remain.
- CI runs the gateway test suite with the same Bun toolchain used locally.

## Phase 4.12 — Phase Integration & Exit Criteria

**Status:** ⏳ Planned

Phase 4 is complete when the gateway is a stable, independently testable service connecting the completed Phase 1–3 platform to the future dashboard.

### Required outcomes

- [ ] TypeScript gateway runs under Bun.
- [ ] Bun is the package manager and test/runtime workflow.
- [ ] Strict typed configuration is implemented.
- [ ] C++ engine TCP integration works with the existing protocol.
- [ ] Engine reconnect and disconnect handling works.
- [ ] Typed event normalization is implemented.
- [ ] REST API is validated and tested.
- [ ] WebSocket streaming is implemented and tested.
- [ ] Client subscriptions are isolated correctly.
- [ ] Slow-client/backpressure handling is bounded.
- [ ] Python analytics integration works.
- [ ] Gateway logging is operational and configurable.
- [ ] Gateway metrics are exposed.
- [ ] Input validation and security boundaries are implemented.
- [ ] Unit and integration tests pass.
- [ ] CI validates the gateway using Bun.
- [ ] Documentation and API contracts are updated.
- [ ] No regression is introduced into Phases 1–3.

**Phase 4 overall status:** ⏳ Planned

# Phase 5 — React Dashboard

**Status:** ⏳ Planned

Planned:

- Live market data
- Order-book visualization
- Recent trades
- VWAP / SMA / EMA / volatility charts
- Position and P&L display
- Equity curve
- Drawdown visualization
- Risk-event display
- Connection and engine status
- Real-time updates

---

# Phase 6 — Historical Analytics

**Status:** ⏳ Planned

Planned:

- Historical trade queries
- Historical analytics queries
- Historical position queries
- Historical risk-event queries
- Query optimization
- Indexing strategy
- Retention strategy
- Reporting APIs

> PostgreSQL infrastructure is already implemented in Phase 3.8; this phase focuses on historical-data access and user-facing analytics rather than initial database integration.

---

# Phase 7 — Authentication & Security

**Status:** ⏳ Planned

Planned:

- Authentication
- Authorization
- Token management
- Role-based access control
- Input validation
- Rate limiting
- Audit logging
- Secret management
- Secure configuration
- Security testing

---

# Phase 8 — Platform Observability

**Status:** ⏳ Planned

Planned:

- Structured logging
- Prometheus metrics
- Grafana dashboards
- Health checks
- Readiness checks
- Liveness checks
- Distributed tracing
- Error tracking
- Resource monitoring

Target metrics include:

```text
Orders/sec
Trades/sec
Matching latency
Transport latency
Socket connections
Message throughput
Analytics processing latency
Risk evaluation latency
API latency
Error rate
CPU usage
Memory usage
```

---

# Phase 9 — Deployment & Infrastructure

**Status:** ⏳ Planned

Planned:

- Docker images
- Docker Compose environment
- Nginx reverse proxy
- Service networking
- Environment configuration
- Container health checks
- Production-like local environment
- Deployment documentation
- Operational runbook

Target services:

```text
C++ Trading Engine
Python Analytics
Node.js Gateway
React Dashboard
PostgreSQL
Prometheus
Grafana
Nginx
```

---

# Phase 10 — Performance & Production Hardening

**Status:** ⏳ Planned

Planned:

- Performance benchmarking
- Load testing
- Stress testing
- Latency benchmarking
- Memory profiling
- CPU profiling
- Concurrency testing
- Failure injection
- Network fault testing
- Recovery testing
- Resource-exhaustion testing
- Security review
- Performance regression testing
- Deployment validation
- Production-readiness review

---

# Overall Progress Summary

| Phase | Component | Status |
| --- | --- | --- |
| 1 | C++ Order Book & Matching Engine | ✅ Complete |
| 2 | C++ TCP Transport | ✅ Complete |
| 3.1 | Analytics Foundation | ✅ Complete |
| 3.2 | Domain Models | ✅ Complete |
| 3.3 | Technical Indicators | ✅ Complete |
| 3.4 | Socket Ingestion | ✅ Complete |
| 3.5 | Streaming Analytics | ✅ Complete |
| 3.6 | Risk Analytics | ✅ Complete |
| 3.7 | Risk Limits & Risk Events | ✅ Complete |
| 3.8 | PostgreSQL Persistence & Observability | ✅ Complete |
| 3.9 | Metrics & Observability | ✅ Complete |
| 3.10 | Analytics Service Hardening | ⏳ Planned |
| 4 | Node.js Gateway (TypeScript + Bun) | ⏳ Planned |
| 5 | React Dashboard | ⏳ Planned |
| 6 | Historical Analytics | ⏳ Planned |
| 7 | Authentication & Security | ⏳ Planned |
| 8 | Platform Observability | ⏳ Planned |
| 9 | Deployment & Infrastructure | ⏳ Planned |
| 10 | Performance & Production Hardening | ⏳ Planned |

---

# Phase 3 Completion Checklist

### Completed

- [X] Python analytics foundation
- [X] Domain models
- [X] Technical indicators
- [X] Socket ingestion
- [X] Streaming processor
- [X] Analytics publisher
- [X] Analytics service orchestration
- [X] Position and P&L tracking
- [X] Drawdown tracking
- [X] Risk manager
- [X] Risk limits
- [X] Risk events
- [X] PostgreSQL connection factory
- [X] PostgreSQL repositories
- [X] Repository factory
- [X] Application persistence wiring
- [X] End-to-end persistence
- [X] Persistence transaction boundary
- [X] Persistence failure handling
- [X] Persistence metrics and health checks
- [X] Migration lifecycle

### Next

- [ ] Service-wide metrics
- [ ] Processing latency metrics
- [ ] Throughput metrics
- [ ] Risk evaluation metrics
- [ ] Error counters
- [ ] Prometheus integration
- [ ] Grafana dashboards
- [X] Service-wide health/readiness metrics

---

# Architecture at the Current Milestone

```text
                         ┌─────────────────────────┐
                         │    React Dashboard      │
                         │        Phase 5          │
                         └────────────┬────────────┘
                                      │
                              WebSocket / HTTP
                                      │
                         ┌────────────▼────────────┐
                         │     Node.js Gateway     │
                         │        Phase 4          │
                         └────────────┬────────────┘
                                      │
                               Trading / Events
                                      │
              ┌───────────────────────▼───────────────────────┐
              │              C++ Trading Engine               │
              │                    Phases 1–2                 │
              └───────────────────────┬───────────────────────┘
                                      │
                                  TRADE Events
                                      │
                         ┌────────────▼────────────┐
                         │    Python Analytics     │
                         │        Phase 3          │
                         │                         │
                         │ SocketClient             │
                         │      ↓                  │
                         │ Message Parser           │
                         │      ↓                  │
                         │ StreamingProcessor       │
                         │   ↙           ↘          │
                         │Indicators     Risk        │
                         │   ↘           ↙          │
                         │ ProcessedTrade            │
                         └────────────┬────────────┘
                                      │
                           Persistence / Health
                                      │
                         ┌────────────▼────────────┐
                         │       PostgreSQL         │
                         │        Phase 3.8         │
                         └─────────────────────────┘
```
