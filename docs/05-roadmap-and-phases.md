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

**Latest Completed Milestone:** Phase 4.8.5 — Rate-Limit Boundary

**Current Milestone:** Phase 4.8 — Security Boundaries & Input Hardening

### Current validated path

```text
C++ Matching Engine
        ↓
C++ TCP Transport
        ↓
Gateway Engine Event Client
        ↓
Gateway normalization
        ↓
Gateway Analytics Client
        ↓
Python Gateway Analytics Receiver
        ↓
Phase 4.6.1 contract validation
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
        ↓
Bidirectional analytics TCP output
        ↓
Gateway analytics state + WebSocket
```

The Node.js gateway now provides the browser-facing HTTP boundary and a typed normalization layer for upstream engine messages. Phase 4.5 connects the live C++ TCP event stream to the WebSocket hub for real-time TRADE delivery.

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

**Status:** 🚧 In Progress

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

**Status:** ✅ Complete

Implemented:

- Independently runnable Bun/TypeScript gateway.
- Fastify application bootstrap.
- Graceful and idempotent start/stop lifecycle.
- Gateway health endpoint.
- Baseline unit and integration test infrastructure.
- Clear configuration boundary.
- Gateway source/test structure.

## Phase 4.2 — Configuration & Environment Management

**Status:** ✅ Complete

Implemented:

- Gateway host and port configuration.
- C++ engine host and port configuration.
- Analytics connection settings.
- WebSocket configuration.
- HTTP timeout and body-size limits.
- Reconnection parameters and validation.
- Logging configuration.
- CORS configuration and runtime integration.
- Prometheus metrics configuration and runtime endpoint.
- Immutable typed configuration.
- Deterministic validation errors.
- Complete gateway `.env.example`.

Validation:

- Gateway TypeScript build passes.
- Gateway test suite: 21 passed, 0 failed.
- CORS integration coverage passes.
- Metrics integration coverage passes.

## Phase 4.3 — Gateway HTTP API

**Status:** ✅ Complete

Expose a stable, versioned application API without duplicating engine or analytics domain logic.

Implemented:

- Established the `/api/v1/...` route boundary.
- Added request and response schemas.
- Validated path, query, and body inputs.
- Defined consistent HTTP status codes.
- Defined deterministic REST error responses.
- Added upstream timeout/error mapping.
- Preserved `/health` and the configured Prometheus endpoint.
- Added route-level unit/integration tests.
- Updated API documentation with implemented contracts.

Initial application surface:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | /api/v1/status | Engine/analytics connection status |
| GET | /api/v1/market | Current market state |
| GET | /api/v1/orderbook | Current order-book snapshot |
| GET | /api/v1/trades | Recent trades |
| GET | /api/v1/analytics | Latest analytics state |
| POST | /api/v1/engine/start | Simulation control |
| POST | /api/v1/engine/stop | Simulation control |
| POST | /api/v1/engine/reset | Simulation reset |

Historical query APIs remain deferred to Phase 6 unless a minimal read-through contract is required earlier.

Exit criteria:

- Every implemented route has an explicit contract.
- Invalid requests return deterministic client errors.
- Upstream failures map to documented API errors.
- Integration tests cover success and failure paths.
- API documentation matches the implementation.

## Phase 4.4 — Engine Protocol & Event Normalization

**Status:** ✅ Complete

Create a stable gateway-facing event model around upstream engine messages.

Implemented:

- Typed TypeScript representations for supported engine messages.
- JSON validation and deterministic normalization.
- 4-byte big-endian length-prefixed engine-frame decoding.
- Fragmented and multiple-frame handling.
- Fatal UTF-8 validation.
- Existing 1 MiB maximum payload enforcement.
- Explicit engine message types: HELLO, HEARTBEAT, ORDER, TRADE, MARKET_DATA, BOOK_SNAPSHOT, ERROR, and SHUTDOWN.
- Typed TRADE payload validation for symbol, price, quantity, taker/maker order identity, taker side, and buy/sell order identity.
- Normalized typed TRADE events preserving event identity and trading fields.
- Explicit rejection of malformed messages and unsupported event types.
- Consistent normalized event representation for downstream gateway consumers.
- Unit coverage for frame decoding, message parsing/normalization, event normalization, and TRADE validation.

Phase 4.4 establishes the event contract used by the WebSocket layer in Phase 4.5.

## Phase 4.5 — WebSocket Gateway

**Status:** ✅ Complete

Provide real-time browser streaming without exposing internal services directly.

Implemented in the current milestone:

- Configurable WebSocket endpoint at `WEBSOCKET_PATH`.
- WebSocket connection lifecycle management.
- Explicit subscribe/unsubscribe protocol for supported event types.
- Typed TRADE event serialization using the Phase 4.4 normalized event model.
- Server ping/pong heartbeat and dead-client cleanup.
- Per-client bounded outbound queues.
- Slow-consumer protection by closing clients whose queues exceed `WEBSOCKET_MAX_QUEUE_SIZE`.
- Graceful gateway shutdown that stops heartbeat processing and closes active clients.
- Unit coverage for connection setup, subscriptions, event delivery, invalid messages, and queue limits.

Remaining scope:

- Connected the hub to the live upstream engine event source through the Gateway engine event client.
- Added end-to-end WebSocket integration coverage against a fake TCP engine source.
- Expanded live TRADE delivery through the normalized Phase 4.4 event model.

Exit criteria:

- Clients can establish and close WebSocket connections deterministically.
- Supported normalized engine events can be serialized and delivered to subscribed clients.
- Heartbeat/ping-pong behavior is bounded and tested.
- Dead or slow clients do not block other clients.
- Queue/backpressure limits are enforced deterministically.
- Gateway shutdown closes active WebSocket clients cleanly.
- WebSocket behavior is covered by automated tests.

## Phase 4.6 — Python Analytics Integration

**Status:** ✅ Complete

Integrate the completed analytics service without duplicating analytics calculations.

### Phase 4.6.1 — Gateway ↔ Python Analytics Contract

**Status:** ✅ Complete

Implemented:

- Versioned Gateway-to-analytics TRADE envelope.
- Stable event and request identity contract.
- ISO-8601 timestamp validation with timezone requirement.
- Positive price and quantity validation.
- Taker/maker and buy/sell order identity validation.
- BUY/SELL taker-side validation.
- Python contract validation layered on the existing MessageParser and Trade model.
- Cross-service contract tests for valid and invalid TRADE messages.
- Preserved the existing nested JSON-string payload representation used by Python analytics.

### Phase 4.6.3 — Python Analytics Receiver

**Status:** ✅ Complete

Implemented:

- Added a dedicated Python TCP receiver for Gateway-to-analytics traffic.
- Reused the existing 4-byte big-endian length-prefixed framing.
- Preserved the existing 1 MiB maximum payload boundary.
- Added fragmented and multiple-frame decoding.
- Added UTF-8 validation and deterministic transport-protocol errors.
- Added clean Gateway connect/disconnect lifecycle handling.
- Added support for a new Gateway connection after disconnect.
- Routed complete raw messages into the existing AnalyticsService backpressure queue.
- Reused the Phase 4.6.1 GatewayTradeMessage contract and existing MessageParser/Trade domain model.
- Added receiver transport and configuration tests.

The receiver intentionally does not duplicate analytics calculations or domain validation.

### Phase 4.6.2 — Gateway Analytics Client

**Status:** ✅ Complete

Implemented:

- Dedicated Gateway-to-Python analytics TCP client.
- Existing 4-byte big-endian framed UTF-8 transport.
- Phase 4.6.1 versioned TRADE contract serialization.
- Bounded disconnected outbound queue.
- Exponential reconnect and connection timeout handling.
- Separate analytics connection lifecycle logging.
- Graceful Gateway shutdown integration.
- Client transport and queue tests.

### Phase 4.6.4 — Analytics Output Back to Gateway

**Status:** ✅ Complete

Implemented:

- Extended the versioned analytics contract with ANALYTICS_UPDATE and RISK_EVENT.
- Reused the existing Gateway ↔ Python TCP connection as a bidirectional analytics transport.
- Added Gateway-side framed output decoding with fragmented and multiple-frame handling.
- Added Python outbound framing through the active Gateway receiver connection.
- Published AnalyticsResult and RiskEvent without duplicating analytics calculations.
- Added Gateway-owned latest analytics snapshot state for /api/v1/analytics.
- Added ANALYTICS_UPDATE and RISK_EVENT WebSocket event types.
- Connected live engine and analytics connection state to /api/v1/status.
- Added cross-service contract, transport, provider, and serialization tests.

### Phase 4.6 exit status

The Phase 4.6 Gateway ↔ Python analytics integration milestones 4.6.1–4.6.4 are complete. Runtime validation against the full C++ engine/PostgreSQL stack remains part of the broader Phase 4.10 integration-validation work.

## Phase 4.7 — Error Handling, Resilience & Backpressure

**Status:** ✅ Complete

Phase 4.7 establishes bounded failure handling, recovery, liveness monitoring, and graceful degradation across Gateway engine and analytics boundaries.

### Phase 4.7.1 — Error Model & Failure Boundaries

**Status:** ✅ Complete

- Stable connection, timeout, protocol, validation, queue-overflow, dependency-unavailable, processing, and shutdown failure categories.
- Explicit recoverability semantics.
- Python analytics integration failure types and tests.
- Gateway failure types, classification, and tests.
- Documented logging, recovery, queue, and connection-close boundaries.

### Phase 4.7.2 — Engine Connection Resilience

**Status:** ✅ Complete

- Hardened engine socket lifecycle handling.
- Isolated protocol state per socket and ignored stale socket events.
- Classified connection, timeout, and protocol failures through the Phase 4.7 error model.
- Preserved bounded reconnect/backoff behavior.
- Added reconnect and failure-classification coverage.

### Phase 4.7.3 — Engine Health & Liveness Monitoring

**Status:** ✅ Complete

- Exposed engine connection state and health timestamps.
- Tracked last message and heartbeat activity.
- Tracked reconnect attempts and health events.
- Added Prometheus engine health/liveness metrics.
- Added `GET /api/v1/status/engine`.
- Added focused health, metrics, and status integration coverage.

### Phase 4.7.4 — Engine Liveness Failure & Recovery

**Status:** ✅ Complete

- Added configurable `ENGINE_HEARTBEAT_TIMEOUT_MS` with a 15-second default.
- Reset the liveness deadline after every valid engine HEARTBEAT.
- Emitted a dedicated `liveness_timeout` health event for stale heartbeats.
- Reused the existing reconnect lifecycle for recovery.
- Added `gateway_engine_liveness_failures_total` Prometheus telemetry.
- Added liveness recovery and continuous-heartbeat coverage.

### Phase 4.7.5 — Analytics Backpressure & Graceful Degradation

**Status:** ✅ Complete

- Classified analytics outbound queue saturation as `queue_overflow`.
- Preserved engine and WebSocket processing when analytics is unavailable or its bounded queue is full.
- Emitted a dedicated analytics queue-overflow health event.
- Added `gateway_analytics_queue_overflows_total` Prometheus telemetry.
- Added focused queue-overflow classification and metrics coverage.

**Phase 4.7 exit status:** ✅ Complete

## Phase 4.8 — Security Boundaries & Input Hardening

## Phase 4.8.6 — AuthN/AuthZ Boundary Preparation

**Status:** 🚧 Complete on milestone branch; pending merge

Implemented:

- Explicit authenticated/unauthenticated request state.
- Authenticated principal model with subject, roles, and scopes.
- Reusable authentication and authorization guards.
- Injectable Gateway authentication resolver seam.
- Opt-in authentication enforcement via AUTH_ENABLED and AUTH_ENFORCEMENT_ENABLED.
- Enforcement remains disabled by default.
- No bearer-token parsing or credential verification is introduced until a concrete identity provider contract is selected.
- Existing sanitized UNAUTHORIZED and FORBIDDEN public error contracts remain the external failure boundary.

Environment variables:

- AUTH_ENABLED
- AUTH_ENFORCEMENT_ENABLED

Future 4.8.x work can provide the concrete credential verifier/identity-provider adapter and route-level authorization policy without changing the Gateway's core request boundary.



## Phase 4.8.5 — Rate-Limit Boundary

**Status:** 🚧 Complete on milestone branch; pending merge

Implemented:

- Bounded in-process HTTP fixed-window rate limiting.
- Per-client request buckets keyed by the gateway-observed remote address.
- Configurable request count, window duration, maximum retained client buckets, and enable/disable control.
- Stable HTTP 429 response using the public RATE_LIMITED error code.
- Retry-After response header for rejected requests.
- Explicit exclusions for /api/health and /metrics.
- Prometheus rejection metric: gateway_rate_limit_rejections_total.
- Structured rate-limit rejection logging.
- Configuration and runtime regression coverage.

Default boundary:

| Setting | Default |
| --- | ---: |
| Enabled | true |
| Maximum requests | 120 |
| Window | 60 seconds |
| Maximum retained clients | 10,000 |

Environment variables:

- RATE_LIMIT_ENABLED
- RATE_LIMIT_MAX_REQUESTS
- RATE_LIMIT_WINDOW_MS
- RATE_LIMIT_MAX_CLIENTS

The limiter is intentionally in-process for the current single-gateway simulation. A shared store can be introduced later if horizontally scaled gateway instances require a distributed rate-limit boundary.



**Status:** 🚧 In Progress

Harden external inputs, CORS, request/message sizes, error exposure, rate-limit hooks, and future authentication/authorization boundaries.

## Phase 4.9 — Operational Logging & Metrics

**Status:** ⏳ Planned

Extend structured operational logging and metrics across gateway HTTP, upstream connections, and WebSocket behavior. The basic Prometheus exposition endpoint is already implemented in Phase 4.2; this milestone adds the broader metric set and operational instrumentation.

## Phase 4.10 — Testing & Integration Validation

**Status:** ⏳ Planned

Complete gateway unit, integration, contract, failure-recovery, and end-to-end validation using the Bun toolchain.

## Phase 4.11 — Phase Integration & Exit Criteria

**Status:** ⏳ Planned

Phase 4 is complete when the gateway connects the completed Phase 1–3 platform to the future dashboard with validated REST/WebSocket contracts, resilience, security boundaries, observability, tests, and CI coverage.

**Phase 4 overall status:** 🚧 In Progress — 4.1 through 4.7 complete; 4.8 is the active milestone.

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
| 3.10 | Analytics Service Hardening | ✅ Complete |
| 4.1 | Gateway Foundation & Architecture | ✅ Complete |
| 4.2 | Gateway Configuration & Runtime Hardening | ✅ Complete |
| 4.3 | Gateway HTTP API | ✅ Complete |
| 4.4 | Engine Protocol & Event Normalization | ✅ Complete |
| 4.5 | WebSocket Gateway | ✅ Complete |
| 4.6 | Python Analytics Integration | 🚧 In Progress |
| 4.7 | Error Handling, Resilience & Backpressure | 🚧 In Progress |
| 4.8 | Security Boundaries & Input Hardening | ⏳ Planned |
| 4.9 | Operational Logging & Metrics | ⏳ Planned |
| 4.10 | Testing & Integration Validation | ⏳ Planned |
| 4.11 | Phase Integration & Exit Criteria | ⏳ Planned |
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
                         │   Phases 4.1–4.5       │
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
