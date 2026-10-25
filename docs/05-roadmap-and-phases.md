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

**Overall Status:** 🚧 In Progress — Phase 5 is now the active product-development milestone.

**Latest merged implementation milestones:** Phase 5.14 analytics PostgreSQL connection-recovery hardening (PR #138), pytest warning cleanup (PR #139), deterministic Gateway Analytics TCP-client reconnect regression coverage (PR #140; merge commit `a36d757ad6e051c074e092593f97396ab1564494`), C++ engine SIGINT/SIGTERM graceful-shutdown handling (PR #146; merge commit `9627490`), explicit analytics snapshot-readiness errors (PR #148; merge commit `e0eb010`), risk-halt diagnostics and journal-replay regression coverage (PR #156; merge commit `180d033aaede7c06ac78f7a248f5e86cf5f65b23`), persisted trigger diagnostics in snapshot v3 (PR #161; merge commit `f89dbd160b106dca851ef6675807a1ca7f0e0382`), durable journal trade-history reconciliation for Gateway reconnects (PR #162; merge commit `bbf84fa`), and version-4 reconstruction of missing risk-halt diagnostics as recovery-time context (PR #165; merge commit `be2651233efa9b3d13b4ca355751361aca26e8da`). The merged `main` C++ source was clean-built locally and all 16 CTest tests passed; CI was reported green. This does not replace the outstanding live-runtime event-delivery and recovery acceptance checks. PR #162 is deployed and its 23-record Gateway reconciliation was observed in runtime logs. The isolated restart-persistence regression for a newly triggered halt passed on 2026-10-24 using disposable temporary state. On 2026-10-24, isolated Gateway WebSocket E2E, Gateway full-stack integration, and dashboard browser reconnection tests also passed. The browser test uses mocked HTTP endpoints and an intercepted WebSocket; live-runtime browser event delivery remains unverified. The existing live legacy halt still has unavailable trigger fields, and Phase 5.14 remains in progress.

**Current milestone:** Phase 5.14 — Full Runtime Integration Validation

**Phase 4 overall status:** ✅ Complete

Phase 4.10.1 validated the real backend runtime path in CI. Phase 4.11 completed the Phase 4 exit criteria. The validated backend path is production-like for the trading/analytics services, but the user-facing React dashboard and later production-platform work remain planned.

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

| Sub-phase | Area                        | Status      |
| --------- | --------------------------- | ----------- |
| 3.10.1    | Service lifecycle hardening | ✅ Complete |
| 3.10.2    | Configuration validation    | ✅ Complete |
| 3.10.3    | Resource cleanup            | ✅ Complete |
| 3.10.4    | Backpressure handling       | ✅ Complete |
| 3.10.5    | Failure recovery            | ✅ Complete |
| 3.10.6    | Operational logging         | ✅ Complete |

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

| Area                      | Decision                                      |
| ------------------------- | --------------------------------------------- |
| Language                  | TypeScript                                    |
| Runtime                   | Bun                                           |
| Package manager           | Bun                                           |
| HTTP framework            | Fastify                                       |
| WebSocket transport       | ws                                            |
| Validation                | Zod                                           |
| Testing                   | Bun test                                      |
| Logging                   | Pino                                          |
| Metrics                   | Prometheus-compatible metrics                 |
| Configuration             | Typed environment configuration               |
| Upstream engine transport | TCP client using the existing engine protocol |
| External client transport | REST + WebSocket                              |
| Wire format               | Existing JSON contracts / schemas             |

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

| Method | Endpoint             | Purpose                            |
| ------ | -------------------- | ---------------------------------- |
| GET    | /api/v1/status       | Engine/analytics connection status |
| GET    | /api/v1/market       | Current market state               |
| GET    | /api/v1/orderbook    | Current order-book snapshot        |
| GET    | /api/v1/trades       | Recent trades                      |
| GET    | /api/v1/analytics    | Latest analytics state             |
| POST   | /api/v1/engine/start | Simulation control                 |
| POST   | /api/v1/engine/stop  | Simulation control                 |
| POST   | /api/v1/engine/reset | Simulation reset                   |

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

Completed runtime integration:

- Connected the hub to the live upstream engine event source through the Gateway engine event client.
- Added end-to-end WebSocket integration coverage against a TCP engine source.
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

### Phase 4.7 — Known Issue: Gateway Did Not Auto-Recover from a Container Recreation During Phase 5.14 Acceptance (observed 2026-10-22)

**Status:** Open — discovered during Phase 5.14 runtime validation

During Phase 5.14 acceptance work on 2026-10-22, the running engine container was stopped for approximately 30 seconds to allow a scratch-volume test, then restarted. The live engine restarted cleanly and returned to its persisted halt state; however, the gateway's engine event client did not reconnect on its own. `GET /api/v1/status` continued to return `{"gateway":"ok","engine":"disconnected","analytics":"connected"}`, and no further engine-connection log lines appeared in the gateway's log stream after the initial disconnect. The gateway's HTTP layer remained healthy throughout.

The unit and integration test coverage for Phase 4.7.4 exercises bounded reconnect/backoff for isolated engine disconnects. The observed behavior indicates that at least one of the following is true:

- the retry budget is exhausted before a 30-second outage can be recovered, or
- the client enters a terminal disconnected state without further retry, or
- the client's DNS/socket state is stale after the engine container is recreated with the same hostname.

**Workaround (verified):** `docker compose restart gateway` restores the engine connection immediately after restart; `GET /api/v1/status` returns `{"engine":"connected"}` on the next poll.

**Not yet established:** whether this is a retry-budget tuning issue (recoverable by increasing retries), a client state-machine bug (recoverable by fixing the terminal-state path), or a container-network/DNS effect (recoverable by adding explicit re-resolution). The gateway logs at the time of the disconnect show no error and no further connection attempts, which is consistent with the client having entered a terminal state silently.

**Follow-up:** investigate `gateway-node/src/engine/engine-event-client.ts` reconnection behavior under prolonged (>=30s) engine unavailability against the running Compose stack. Not part of Phase 5.14 exit criteria; not blocking the closed incident. Tracked separately so the Phase 4.7 milestone's "Complete" status can be re-validated if the finding turns out to be a defect rather than a tuning gap.

**Follow-up (2026-10-22):** symptom mitigated by defensive self-heal (commits `4e6542c` and the diagnostic follow-up). The self-heal reconnects from the "disconnected with no pending timer" state within 5 seconds and emits `engine_event_client_error` when it fires, making the mitigation observable. Root cause **not yet established**. A dedicated diagnostic session is required:

- Instrument `gateway-node/src/engine/engine-event-client.ts` to log every `emitState` call, every `scheduleReconnect` call (including which guard fired, if any), every `handleClose` call (including the guard result), and every `socket` assign/unassign.
- Reproduce the bug: stop the live engine, wait 30s, restart it, observe gateway logs and metrics.
- Identify the code path that transitions the client to `disconnected` without incrementing `gateway_engine_reconnect_attempts_total` or `gateway_engine_connection_failures_total` (the observed evidence from 2026-10-22 was both counters at 0 while the client reported `disconnected` with `reconnectAttempts: 0`).
- Fix the root cause. If the fix is clean, remove the self-heal; if the self-heal is cheap and the fix complex, keep both as defense-in-depth.


**Update (2026-10-22):** A plain engine stop/start (30 seconds of downtime) was verified to auto-recover — the gateway reconnects on its own within ~10 seconds, no gateway restart needed. The Known Issue therefore applies specifically to the container-recreation scenario observed during B2, not to all prolonged outages.

Do not treat the self-heal as proof the root cause is fixed. The self-heal addresses the visible symptom; the underlying state-transition defect is still present.

### Phase 4.7.5 — Analytics Backpressure & Graceful Degradation

**Status:** ✅ Complete

- Classified analytics outbound queue saturation as `queue_overflow`.
- Preserved engine and WebSocket processing when analytics is unavailable or its bounded queue is full.
- Emitted a dedicated analytics queue-overflow health event.
- Added `gateway_analytics_queue_overflows_total` Prometheus telemetry.
- Added focused queue-overflow classification and metrics coverage.

**Phase 4.7 exit status:** ✅ Complete

## Phase 4.8 — Security Boundaries & Input Hardening

**Status:** ✅ Complete

Phase 4.8 is fully integrated on `main`. The security hardening gate covers external input validation, transport/request boundaries, strict CORS, sanitized public errors, rate limiting, and the opt-in authentication/authorization boundary.

### Phase 4.8.7 — Security Regression & Integration Validation

**Status:** ✅ Complete

- Dedicated Gateway security regression command covering Phase 4.8.1–4.8.6.
- CI Gateway build, security regression, and full Gateway test execution.
- Final local Gateway validation: 182 tests passed, 0 failed.
- No new identity provider, credential verifier, or authentication feature was introduced by the validation gate.

### Phase 4.8.6 — AuthN/AuthZ Boundary Preparation

**Status:** ✅ Complete

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

**Status:** ✅ Complete

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

| Setting                  |    Default |
| ------------------------ | ---------: |
| Enabled                  |       true |
| Maximum requests         |        120 |
| Window                   | 60 seconds |
| Maximum retained clients |     10,000 |

Environment variables:

- RATE_LIMIT_ENABLED
- RATE_LIMIT_MAX_REQUESTS
- RATE_LIMIT_WINDOW_MS
- RATE_LIMIT_MAX_CLIENTS

The limiter is intentionally in-process for the current single-gateway simulation. A shared store can be introduced later if horizontally scaled gateway instances require a distributed rate-limit boundary.

**Status:** 🚧 In Progress

Harden external inputs, CORS, request/message sizes, error exposure, rate-limit hooks, and future authentication/authorization boundaries.

## Phase 4.9 — Operational Logging & Metrics

**Status:** Complete

Extend structured operational logging and metrics across gateway HTTP, engine, analytics, and WebSocket boundaries. The basic Prometheus exposition endpoint is already implemented; this milestone focuses on consistent operational instrumentation rather than changing business behavior.

### Phase 4.9 — Operational Logging & Metrics

**Status:** Complete

- **4.9.1 Structured Operational Logging** — Complete
- **4.9.2 Metrics Completion** — Complete
- **4.9.3 Request & Event Correlation** — Complete
- **4.9.4 Health & Readiness Observability** — Complete
- **4.9.5 Operational Failure & Alerting Integration** — Complete
- **4.9.6 Observability Regression & Validation** — Complete

**Phase 4.9 exit status:** Complete

## Phase 4.10 — Testing & Integration Validation

**Status:** Complete

Phase 4.10 closes the gap between isolated service regression suites and the complete multi-service runtime.

Completed:

- Dedicated Gateway contract integration test.
- Real C++ Engine runtime container.
- Real Python Analytics runtime container.
- PostgreSQL runtime with initialized persistence schema.
- Gateway runtime container with REST/WebSocket boundary.
- Configurable C++ Engine bind address for container networking.
- Real Engine TCP → Gateway → Analytics TCP → PostgreSQL → Gateway analytics output path.
- Real WebSocket TRADE and ANALYTICS_UPDATE smoke validation.
- PostgreSQL persistence verification in CI.
- Runtime-stack startup/readiness validation.
- CI coverage for the real Docker Compose stack.
- Disconnect/recovery behavior remains covered by the Engine/Gateway/Analytics service-level resilience suites.

### Phase 4.10.1 — Real Full-Stack Runtime Integration

**Status:** Complete

The production-like local runtime is now defined by the root docker-compose.yml:

    C++ Engine :9000
          │
          ▼
    Node Gateway :8080
          │
          ├──────── TCP ───────► Python Analytics :8000
          │                           │
          │                           ▼
          │                      PostgreSQL :5432
          │                           │
          └◄──── ANALYTICS_UPDATE ───┘
                     │
                     ▼
              WebSocket /ws

Validation:

- docker compose up -d --build
- cd gateway-node && bun test tests/runtime-stack.integration.test.ts
- docker compose down -v

The runtime integration CI job also verifies that at least one real Engine-generated trade is persisted in PostgreSQL.

**Phase 4.10 exit status:** Complete

## Phase 4.11 — Phase Integration & Exit Criteria

**Status:** Complete

Phase 4 exit criteria are satisfied:

- [X] C++ Engine transport is reachable from the Gateway runtime.
- [X] Gateway forwards real TRADE events to Python Analytics.
- [X] Python Analytics processes real TRADE events.
- [X] Analytics results are persisted to PostgreSQL.
- [X] Analytics results return to the Gateway.
- [X] Gateway publishes live analytics to WebSocket consumers.
- [X] Health/readiness and observability boundaries are present.
- [X] Security regression and full Gateway suites pass.
- [X] C++ Debug/Release and Python/PostgreSQL suites pass.
- [X] Runtime stack is validated in CI.
- [X] Phase 4 documentation and exit evidence are recorded.

**Phase 4 overall status:** Complete

# Phase 5 — React Dashboard

**Status:** 🚧 In Progress — next milestone

Phase 5 is the user-facing product layer of the trading platform. The backend runtime and service boundaries are already established in Phases 1–4. The dashboard must consume those existing Gateway REST and WebSocket contracts and must not bypass the Gateway to connect directly to the C++ engine or Python analytics service.

## Phase 5 Objective

Build a production-structured React dashboard that provides:

- Live market state.
- Order-book visualization.
- Recent trade activity.
- Technical analytics.
- Portfolio and P&L state.
- Risk-limit and risk-event visibility.
- Engine, analytics, database/readiness, and WebSocket status.
- Real-time updates through Gateway WebSocket events.
- Clear loading, empty, stale, disconnected, and dependency-error states.
- Responsive desktop, tablet, and mobile layouts.
- Automated dashboard tests.
- Browser-level validation against the real Phase 4 runtime stack.

## Phase 5 Architecture Contract

```text
React Dashboard
      │
      ├── REST ────────────────┐
      │                        │
      └── WebSocket ──────────┤
                               ▼
                       Node.js Gateway
                               │
             ┌─────────────────┴─────────────────┐
             │                                   │
        C++ Trading Engine                Python Analytics
             │                                   │
             └─────────────────┬─────────────────┘
                               ▼
                         PostgreSQL
```

### Dashboard rules

1. React communicates only with the Gateway.
2. REST is used for initial snapshots and request/response data.
3. WebSocket is used for live event delivery.
4. Existing Gateway contracts are the source of truth.
5. Analytics calculations remain in Python; React only renders returned values.
6. The dashboard must remain usable when one upstream dependency is unavailable.
7. Environment-specific Gateway URLs must come from Vite environment configuration.
8. WebSocket reconnects must restore the required subscriptions.
9. Components should be independently testable.
10. UI state must distinguish loading, empty, stale, disconnected, and error conditions.

---

## Phase 5.0 — Repository Inspection & Dashboard Baseline

**Status:** ✅ Complete

Before implementation, establish the actual dashboard scaffold and verify the Gateway contracts that Phase 5 will consume.

### Objectives

- Inspect the existing dashboard-react structure.
- Confirm the existing React/Vite/TypeScript setup.
- Identify the package manager and available scripts.
- Verify the dashboard can build before feature work.
- Inspect implemented Gateway REST and WebSocket contracts.
- Avoid replacing existing working code unnecessarily.

### Inspect

```text
dashboard-react/
├── package.json
├── src/
├── public/
└── ...
```

Gateway contracts to review:

```text
GET /api/v1/status
GET /api/v1/status/engine
GET /api/v1/market
GET /api/v1/orderbook
GET /api/v1/trades
GET /api/v1/analytics
WS /ws
```

### Validation

```text
Install dependencies       PASS
Development server starts  PASS
Production build           PASS
Gateway contract review    PASS
```

### Exit criteria

- [X] Dashboard baseline builds.
- [X] Existing source structure is understood.
- [X] Gateway endpoint contracts are documented for dashboard use.
- [X] No unnecessary backend changes are introduced.

---

## Phase 5.1 — Dashboard Foundation & Application Shell

**Status:** ✅ Complete

Create the reusable frontend foundation before implementing trading views.

### Objectives

- Establish the React application shell.
- Add routing.
- Add dashboard layout.
- Add navigation.
- Add shared UI primitives.
- Establish design tokens and trading-dashboard styling.
- Establish reusable loading, error, empty, and connection-state components.

### Recommended structure

```text
dashboard-react/src/
├── app/
│   ├── App.tsx
│   ├── router.tsx
│   └── providers.tsx
├── components/
│   ├── common/
│   ├── layout/
│   ├── market/
│   ├── orderbook/
│   ├── trades/
│   ├── analytics/
│   ├── portfolio/
│   ├── risk/
│   └── system/
├── hooks/
├── pages/
├── services/
│   ├── api/
│   └── websocket/
├── types/
├── utils/
└── styles/
```

### Application shell

```text
App
 ↓
Router
 ↓
DashboardLayout
 ├── Header
 ├── Sidebar / Navigation
 └── MainContent
```

### Initial routes

```text
/dashboard
/markets
/trades
/analytics
/risk
/system
```

### Shared UI

Create reusable components for:

- Card/panel.
- Metric/stat display.
- Loading state.
- Empty state.
- Error state.
- Connection badge.
- Timestamp/stale-data indicator.
- Responsive grid/container.

### Exit criteria

- [X] Dashboard route renders.
- [X] Navigation works.
- [X] Shared UI primitives exist.
- [X] Design tokens are centralized.
- [X] Desktop and mobile shell layouts render.
- [X] Production build passes.

---

## Phase 5 UI / Visual Design Contract

**Status:** ✅ Defined

Phase 5 uses a fixed visual language so dashboard implementation does not repeatedly revisit the UI direction.

### Visual direction

**Liquid Glass + Bento Grid + Spatial Minimalism**

- **Liquid Glass:** translucent, layered panels with restrained blur and subtle borders.
- **Bento Grid:** modular dashboard composition for market, trades, analytics, portfolio, risk, and system views.
- **Spatial Minimalism:** clear hierarchy, generous spacing, shallow depth, and minimal visual noise.
- **Neomorphism:** limited to small controls only when it improves affordance.
- **Claymorphism:** not used.
- **Skeuomorphism:** not used.
- **Maximalism:** not used.

### Exact three-color palette

The Phase 5 dashboard uses **only these three colors**. No blue, green, red, amber, gray, or additional brand colors may be introduced.

| Color           | Hex         | Usage                                                           |
| --------------- | ----------- | --------------------------------------------------------------- |
| Cream           | `#F8F4E7` | Primary application background, light canvas, readable contrast |
| Chocolate Brown | `#4E342E` | Dark surfaces, primary text, deep states                        |
| Burnt Orange    | `#CC5500` | Brand accent, active states, actions, highlights                |

Opacity variants of these same three colors are allowed for glass, borders, shadows, gradients, and depth.

### Status treatment

Semantic meaning must not introduce additional colors:

- **BUY / PROFIT / healthy** → Burnt Orange `#CC5500` plus explicit label/icon.
- **SELL / LOSS / error / breached** → Chocolate Brown `#4E342E` plus explicit label/icon and structural emphasis.
- **RISK / WARNING / degraded** → Burnt Orange `#CC5500` plus explicit label/icon.
- **Disconnected / neutral** → Cream `#F8F4E7` at reduced opacity on Chocolate Brown.

### UI rules

1. Chocolate Brown, Cream, and Burnt Orange are the only dashboard colors.
2. Opacity variants may be created only from those three colors.
3. Burnt Orange is the primary interactive and active-state accent.
4. Cream provides the primary canvas and overall visual lightness.
5. Chocolate Brown provides dark surfaces, typography, and spatial depth.
6. Glass effects remain restrained; readability always wins over decoration.
7. Trading data must remain visually scannable at a glance.
8. No fabricated market, analytics, P&L, or risk values are introduced for visual polish.
9. Loading, empty, stale, disconnected, and error states use only the three palette colors.
10. New dashboard components must consume centralized tokens rather than introducing arbitrary colors.

### Design reference

This contract is the source of truth for Phase 5 dashboard styling and should be consulted before adding new visual components.

---

## Phase 5.2 — Gateway REST Client & Typed API Models

**Status:** ✅ Complete

Build one typed REST boundary for all initial dashboard snapshots.

### Objectives

- Centralize HTTP communication.
- Keep Gateway URL configurable.
- Define frontend models matching Gateway response contracts.
- Normalize transport errors into dashboard-friendly errors.
- Prevent individual components from implementing their own fetch logic.

### Recommended files

```text
src/services/api/client.ts
src/services/api/status.ts
src/services/api/market.ts
src/services/api/orderbook.ts
src/services/api/trades.ts
src/services/api/analytics.ts

src/types/status.ts
src/types/market.ts
src/types/orderbook.ts
src/types/trade.ts
src/types/analytics.ts
```

### Environment configuration

```text
VITE_GATEWAY_URL
```

No hardcoded environment-specific Gateway URL should exist in components.

### API responsibilities

| Client        | Endpoint              | Responsibility              |
| ------------- | --------------------- | --------------------------- |
| status        | /api/v1/status        | Overall service status      |
| engine status | /api/v1/status/engine | Engine health/liveness      |
| market        | /api/v1/market        | Current market state        |
| orderbook     | /api/v1/orderbook     | Initial book snapshot       |
| trades        | /api/v1/trades        | Recent trades               |
| analytics     | /api/v1/analytics     | Latest analytics/risk state |

### Failure handling

Map:

```text
HTTP 4xx  → client/request error
HTTP 5xx  → Gateway/dependency error
timeout   → request timeout state
network   → disconnected dependency state
invalid   → contract/data error
```

### Exit criteria

- [X] All required REST clients implemented.
- [X] Models match Gateway contracts.
- [X] Gateway URL is environment-driven.
- [X] HTTP errors are normalized.
- [X] REST client tests cover success and failure paths.

---

## Phase 5.3 — WebSocket Client, Protocol & Reconnection

**Status:** ✅ Complete

Create the browser WebSocket layer for live Gateway events.

### Objectives

- Connect to Gateway /ws.
- Subscribe to supported event types.
- Parse and validate incoming events.
- Dispatch events to dashboard state.
- Handle close/error/reconnect.
- Restore subscriptions after reconnect.
- Detect stale connections.

### Recommended files

```text
src/services/websocket/client.ts
src/services/websocket/protocol.ts
src/services/websocket/reconnect.ts
src/hooks/useGatewayWebSocket.ts
```

### Supported dashboard events

```text
TRADE
ANALYTICS_UPDATE
RISK_EVENT
```

### Lifecycle

```text
CONNECT
  ↓
CONNECTED
  ↓
SUBSCRIBE
  ↓
RECEIVE EVENTS
  ↓
CLOSE / ERROR
  ↓
BACKOFF
  ↓
RECONNECT
  ↓
RESUBSCRIBE
  ↓
RECEIVE EVENTS
```

### Failure handling

- Invalid event → reject/ignore safely and record a client-side protocol error.
- Unexpected close → reconnect with bounded backoff.
- Reconnect success → restore subscriptions.
- Repeated failure → expose disconnected state without crashing the UI.
- Stale connection → show stale/disconnected status.

### Exit criteria

- [X] WebSocket connects to Gateway.
- [X] Subscribe/unsubscribe works.
- [X] TRADE events are parsed.
- [X] ANALYTICS_UPDATE events are parsed.
- [X] RISK_EVENT events are parsed.
- [X] Reconnect works.
- [X] Subscriptions are restored after reconnect.
- [X] Invalid messages do not crash the application.
- [X] WebSocket tests pass.

---

## Phase 5.4 — Dashboard Layout & Navigation

**Status:** ✅ Complete

Turn the application shell into the main trading dashboard experience.

### Main dashboard layout

```text
┌─────────────────────────────────────────────────────┐
│ Header: Symbol / Connection / Engine Status         │
├───────────────────────┬─────────────────────────────┤
│ Market Summary        │ Analytics Summary            │
├───────────────────────┼─────────────────────────────┤
│ Price / Analytics     │ Order Book                   │
│ Chart                 │                              │
├───────────────────────┼─────────────────────────────┤
│ Recent Trades         │ Portfolio / Risk             │
├───────────────────────┴─────────────────────────────┤
│ System / Dependency Status                           │
└─────────────────────────────────────────────────────┘
```

### Navigation

```text
Dashboard
Markets
Trades
Analytics
Risk
System
```

### Exit criteria

- [X] All primary pages/routes exist.
- [X] Dashboard has a coherent information hierarchy.
- [X] Navigation works without page reloads.
- [X] Shared header shows connection state.
- [X] Layout adapts to smaller screens.

---

## Phase 5.5 — Live Market Data & Recent Trades

**Status:** ✅ Complete

Connect the first live trading views to the Gateway.

### Market view

Display:

- Symbol.
- Last traded price.
- Last trade quantity.
- Bid.
- Ask.
- Spread when available.
- Market update timestamp.

### Recent trades

Display:

- Trade ID/event ID.
- Symbol.
- Price.
- Quantity.
- Taker side.
- Timestamp.
- Buy order ID.
- Sell order ID.

### Data flow

```text
REST snapshot
     ↓
Initial React state
     ↓
WebSocket TRADE
     ↓
Update trade state
     ↓
Update market summary
     ↓
Render
```

### Requirements

- New TRADE events appear without page refresh.
- Recent-trade history is bounded in the browser.
- Duplicate events are handled deterministically.
- Old/stale data is visibly identified when appropriate.

### Exit criteria

- [X] Initial market state loads from REST.
- [X] Initial trades load from REST.
- [X] Live TRADE events update the UI.
- [X] Market summary updates from live events.
- [X] Duplicate handling is deterministic.
- [X] Loading/empty/error states work.

---

## Phase 5.6 — Order Book Visualization

**Status:** ✅ Complete

Render the current live bid/ask book from the C++ Engine through the Gateway order-book snapshot contract.

### Display

```text
ASKS
Price       Quantity
---------   --------
...

Spread
...

BIDS
Price       Quantity
---------   --------
...
```

### Requirements

- Render bids and asks separately.
- Sort each side according to the Gateway contract.
- Highlight best bid/ask.
- Show quantity/price accurately.
- Handle an empty book.
- Handle unavailable book data.
- Avoid client-side matching or order-book calculation.

### Data flow

```text
GET /api/v1/orderbook
        ↓
Typed snapshot
        ↓
OrderBook component
        ↓
Bid/ask visualization
```

The current implementation uses a request/response snapshot path: Gateway → C++ Engine `BOOK_SNAPSHOT` request → validated live snapshot → `GET /api/v1/orderbook` → React. If a future Gateway WebSocket order-book event is introduced, the component should consume it through the same typed state boundary rather than implementing a second data path.

### Exit criteria

- [X] Snapshot loads correctly from `GET /api/v1/orderbook`.
- [X] Bids/asks render correctly.
- [X] Best bid/ask levels are clear.
- [X] Empty/error states work.
- [X] No trading-engine connection is made from React.
- [X] Live C++ Engine `BOOK_SNAPSHOT` request/response path is integrated through the Gateway.
- [X] Gateway validates order-book symbol, prices, and quantities.
- [X] Market Summary derives Bid, Ask, and Spread from the live order-book snapshot.

---

### Phase 5.6 completion evidence

The completed order-book milestone is integrated on `main` through PR #116, which promotes the stacked Phase 5.6 work from PRs #113–#115.

Implemented:

- C++ Engine synchronized order-book snapshot access protected by engine state locking.
- `BOOK_SNAPSHOT` request/response handling over the existing framed engine protocol.
- Gateway `EngineEventClient` request correlation and timeout handling for order-book snapshots.
- Gateway live order-book provider and `/api/v1/orderbook` integration.
- Validation of order-book symbol, bid/ask arrays, positive finite prices, and safe positive quantities.
- Dashboard rendering of live bids and asks with best-level emphasis.
- Market Summary synchronization using live Best Bid, Best Ask, and Spread.
- Network-independent dashboard deployment through same-origin `/api` and `/ws` reverse proxying.
- Docker/Vite configuration no longer bakes environment-specific Gateway URLs into the dashboard image.

Validation evidence:

```text
C++ CTest suite        PASS — 15/15
Gateway dashboard build PASS
Dashboard tests         PASS — 12/12
Docker runtime          PASS — all 5 services healthy
Gateway readiness       PASS — /api/ready returns 200
Live order-book API     PASS — /api/v1/orderbook returns changing snapshots
```

**Phase 5.6 exit status:** ✅ Complete

### Phase 5.5 completion evidence

The live market/trades foundation is implemented on `main` through PRs #108 and #111.

- Typed Gateway REST client with configurable `VITE_GATEWAY_BASE_URL`.
- Browser WebSocket client for `/ws` with TRADE subscriptions and reconnect/resubscribe behavior.
- Live trading state in the Gateway backed by normalized engine TRADE events.
- Dashboard market summary and bounded recent-trade views.
- Deterministic duplicate trade handling and loading/empty/error states.
- Dashboard shell, responsive navigation, and the 60/30/10 visual system are in place.
- Gateway, engine, analytics, and Docker runtime integration are validated separately.

**Phase 5.5 exit status:** ✅ Complete

## Phase 5.7 — Analytics Charts & Indicator Views

**Status:** ✅ Complete

Render the analytics already calculated by Python. React remains presentation-only and does not recalculate indicators.

### Required analytics

```text
VWAP
SMA
EMA
Volatility
```

Python remains the source of truth for all four indicators. Phase 5.7 adds server-calculated rolling volatility to the existing analytics output contract.

### Requirements

- Consume `/api/v1/analytics` for the latest initial snapshot.
- Consume `ANALYTICS_UPDATE` for live indicator updates.
- Subscribe to `RISK_EVENT` so the view reflects the latest risk state.
- Keep a bounded 120-point browser history for live chart rendering.
- Preserve nullable indicator values until Python has enough observations.
- Preserve server-provided numeric precision.
- Display the source timestamp.
- Do not recalculate analytics in React.
- Handle missing/partial analytics values.

### Recommended views

```text
Price + VWAP
Price + SMA
Price + EMA
Volatility
Analytics summary cards
```

### Data flow

```text
Python Analytics
      ↓
Gateway analytics state
      ↓
REST snapshot / WebSocket update
      ↓
React analytics state
      ↓
Charts
```

### Exit criteria

- [X] VWAP visible.
- [X] SMA visible.
- [X] EMA visible.
- [X] Volatility visible.
- [X] Initial analytics load works.
- [X] Live ANALYTICS_UPDATE works.
- [X] Missing-data states work.
- [X] React performs no duplicate analytics calculation.

---

## Phase 5.8 — Portfolio, P&L & Risk Dashboard

**Status:** ✅ Complete

Expose the portfolio/risk state already produced by Python analytics.

### Portfolio metrics

```text
Position
Average Entry Price
Realized P&L
Unrealized P&L
Equity
Peak Equity
Drawdown
```

### Risk metrics

Display:

- Risk-limit status.
- Warning state.
- Breach state.
- Current value.
- Configured threshold.
- Warning threshold.
- Risk-limit type.
- Symbol.
- Risk-event timestamp.

### Risk events

Consume:

```text
RISK_EVENT
```

Display recent events with clear severity/state.

### Requirements

- No risk calculations in React.
- Preserve Decimal/string precision from the backend contract.
- Distinguish warning and breached states.
- Keep recent risk events bounded.
- Show when risk data is stale.

### Exit criteria

- [X] Portfolio metrics render.
- [X] P&L values render correctly.
- [X] Equity/drawdown state renders.
- [X] Risk status renders.
- [X] RISK_EVENT updates appear live.
- [X] Warning/breach states are visually distinguishable.
- [X] Missing risk data is handled safely.

---

## Phase 5.9 — Engine, Analytics & System Status

**Status:** ✅ Complete

Expose operational health so the dashboard can explain whether missing data is caused by the runtime.

### Status sources

```text
GET /api/v1/status
GET /api/v1/status/engine
WebSocket connection state
```

Where available through the Gateway, surface:

```text
Engine connection
Engine heartbeat/liveness
Analytics connection
Gateway availability
PostgreSQL/readiness state
WebSocket connection
Last update timestamp
```

### Status states

```text
HEALTHY
DEGRADED
DISCONNECTED
STALE
ERROR
```

### Requirements

- Status must be understandable without reading logs.
- A dependency failure must not make the whole dashboard blank.
- Last successful update time should be visible for live data.

### Exit criteria

- [ ] Engine status displayed.
- [ ] Analytics status displayed.
- [ ] WebSocket status displayed.
- [ ] Gateway status displayed.
- [ ] Available database/readiness information displayed.
- [ ] Stale/disconnected conditions are visible.

---

## Phase 5.10 — Loading, Empty, Error & Stale-Data UX

**Status:** ✅ Implementation complete — PR #120 merged

Make dependency and data failures explicit instead of silently showing incorrect values.

Phase 5.10 builds on the existing REST and WebSocket contracts without changing Gateway, Python Analytics, PostgreSQL, or C++ Engine interfaces. The implementation focuses on preserving last-known-good data during transient failures and exposing its freshness clearly.

### Required states

```text
LOADING
EMPTY
READY
STALE
DISCONNECTED
ERROR
```

### Apply to

- Market.
- Trades.
- Order book.
- Analytics.
- Portfolio.
- Risk.
- System status.
- WebSocket connection.

### Rules

- Never display a missing value as a valid zero unless the Gateway contract explicitly says zero.
- Do not replace stale data with fabricated values.
- Preserve the last known valid state when appropriate and mark it stale.
- Error messages shown to users must be concise and safe.

### Exit criteria

- [ ] Every data panel has loading behavior.
- [ ] Every data panel has an empty state.
- [ ] Every data panel has an error state.
- [ ] Stale data is identifiable.
- [ ] WebSocket disconnect/reconnect is visible without clearing valid data.
- [ ] Last-known-good data is preserved during transient failures.
- [ ] Recovery returns the UI to READY/LIVE state.
- [ ] Shared freshness semantics are used across live dashboard pages.
- [ ] Build and existing frontend tests remain green.

---

## Phase 5.11 — Responsive UI & Accessibility

**Status:** ✅ Implementation complete for the current dashboard production-polish scope

The milestone implementation is present, but do not infer that every responsive/accessibility acceptance item has been independently audited solely from CI. Track explicit evidence for the checklist below as part of the remaining dashboard closeout.

Make the dashboard usable across laptop, tablet, and mobile displays.

### Targets

```text
Desktop / Laptop
Tablet
Mobile
```

### Requirements

- Responsive grid layout.
- Collapsible navigation.
- Horizontally scrollable dense tables where necessary.
- Touch-friendly controls.
- Readable typography.
- Keyboard-accessible navigation.
- Visible focus states.
- Semantic headings and labels.
- Charts remain readable on smaller screens.

### Exit criteria

- [ ] Desktop layout works.
- [ ] Tablet layout works.
- [ ] Mobile layout works.
- [ ] Navigation remains usable.
- [ ] Dense trading data remains readable.
- [ ] Basic keyboard accessibility passes.

---

## Phase 5.12 — Halted-State Market Data

**Status:** ✅ Complete — merged in PR #132

Fix the market-data path so live simulated prices remain available when the engine's persisted risk state is halted, without changing the risk boundary.

Implemented:

- C++ engine emits `MARKET_DATA` before the risk-halt matching guard.
- Gateway validates and normalizes market-data events.
- Gateway updates the `GET /api/v1/market` snapshot and publishes `MARKET_DATA` over WebSocket.
- Dashboard subscribes to market-data events and updates the live price.
- Only actual `TRADE` events enter trade history and the analytics pipeline.
- Protocol documentation and tests distinguish market ticks from executed trades.

Local validation:

- Gateway health and readiness returned HTTP 200; engine and analytics were connected.
- `GET /api/v1/market` returned HTTP 200.
- Ten consecutive polls showed advancing timestamps and changing prices at two-second intervals.
- Dashboard showed Gateway connected, WebSocket open, a live market price, and zero trades.

Risk boundary:

- No risk snapshot was reset.
- No risk limit was changed.
- No halt bypass was added.
- Market-data validation does not require generating trades.

---

## Phase 5.13 — Data Integrity & Observability

**Status:** ✅ Implementation hardening merged — PRs #133 and #134

Merged work prevents callbacks from replaced WebSocket connections from mutating state, makes subscribe/unsubscribe idempotent, protects newer live market state from stale REST responses, and reconciles recent live executions with REST trade snapshots using bounded ID-based deduplication. Automated CI passed for both merged pull requests. These changes do not by themselves prove browser-level recovery; that remains a Phase 5.14 runtime validation requirement.

Validate dashboard event correctness, freshness, ordering, and recovery before full runtime closeout.

### Data-integrity guarantees

- `MARKET_DATA` updates market state but never creates a trade record.
- Only `TRADE` events are forwarded to analytics as executions.
- REST market snapshots and WebSocket market events converge on the latest accepted price.
- Stale/disconnected state is shown when live updates stop and clears after recovery.
- Reconnect restores subscriptions without duplicating or corrupting displayed state.
- Sequence/order handling does not allow older market events to overwrite newer state.
- Risk-halt behavior is tested without resetting risk state or bypassing enforcement.

### Test layers

```text
Unit
  ↓
Component
  ↓
Service/API
  ↓
WebSocket
  ↓
Browser E2E
```

### Unit/component coverage

Test:

- Formatters.
- Data normalization.
- Metric cards.
- Market components.
- Trade table.
- Order book.
- Analytics cards/charts.
- Portfolio/risk components.
- Status components.
- Loading/error/empty states.

### REST tests

Cover:

```text
200 success
4xx failure
5xx failure
timeout
network failure
malformed response
```

### WebSocket tests

Cover:

```text
connect
subscribe
event receive
invalid event
close
error
reconnect
resubscribe
stale state
```

### State tests

Verify:

- REST snapshot + WebSocket event ordering.
- Duplicate event handling.
- Reconnect state recovery.
- Bounded recent-event history.
- Stale-state transitions.

### Browser E2E

Critical flow:

```text
Open Dashboard
     ↓
Gateway connection established
     ↓
REST snapshots loaded
     ↓
WebSocket connected
     ↓
TRADE received
     ↓
Market/trades UI updates
     ↓
ANALYTICS_UPDATE received
     ↓
Analytics UI updates
     ↓
RISK_EVENT received
     ↓
Risk UI updates
```

### Exit criteria

- [ ] Unit tests pass.
- [ ] Component tests pass.
- [ ] REST tests pass.
- [ ] WebSocket tests pass.
- [ ] Browser E2E critical flow passes.
- [ ] No known console errors remain.

---

### Phase 5.14 — Dashboard WebSocket Recovery Regression Coverage

**Status:** Automated client-level recovery coverage expanded; full runtime integration remains in progress.

The dashboard WebSocket test suite covers subscription registration and idempotency, unexpected disconnect/reconnect, restoration of subscriptions after a replacement socket opens, ignoring stale callbacks from obsolete sockets, and manual disconnect suppression of pending reconnects. These are fake-socket tests and do not establish browser-level delivery or recovery against the running Docker Compose stack.

## Phase 5.14 — Full Runtime Integration Validation

**Status:** 🚧 In Progress — live runtime smoke validation passed on 2026-10-12, and the Gateway full-stack integration test passed (1 test, 11 assertions). Remaining exit criteria are a fresh trade/risk event proven through the running Compose stack and browser-level WebSocket recovery validation.

Validate the dashboard against the real backend stack rather than mocks alone.

### Runtime

```text
PostgreSQL
    ↑
Python Analytics
    ↑
Node.js Gateway
    ↑
React Dashboard
    ↑
C++ Trading Engine
```

### Read-only local smoke checks

With the existing Docker Compose stack already running, execute:

```bash
bash scripts/validate-runtime.sh
```

The script checks:

- Gateway health and readiness endpoints.
- Market and recent-trade REST responses are successful JSON.
- Dashboard HTTP response is non-empty.
- Analytics Prometheus metrics endpoint responds with content.
- PostgreSQL accepts connections and a read-only `SELECT 1` succeeds.

### Validation evidence — 2026-10-12

- `bash scripts/validate-runtime.sh`: exit code **0**. Gateway health/readiness, market snapshot, recent trades, dashboard HTTP, analytics Prometheus metrics, and PostgreSQL readiness plus read-only `SELECT 1` all passed.
- `docker compose ps -a`: all five services (gateway, engine, analytics, dashboard, PostgreSQL) reported healthy.
- Gateway metrics at validation time: `gateway_ready 1`, `gateway_engine_connected 1`, `gateway_analytics_connected 1`, `gateway_engine_connection_failures_total 0`, and `gateway_analytics_errors_total 0`.
- `cd gateway-node && bun test tests/full-stack.integration.test.ts`: **1 pass, 0 failures, 11 assertions**. The isolated integration test exercises Engine TRADE handling, analytics update/risk events, REST routes, and WebSocket consumers; it is not proof that a new event traversed the running Compose stack.
- The initial stale host-port forwarding was cleared, after which the gateway became healthy and readiness returned HTTP 200 with both dependencies connected.

### Validation evidence — 2026-10-14 — Graceful-shutdown recovery checkpoint

- PR #146 merged the C++ engine SIGINT/SIGTERM shutdown handling; merge commit: `9627490`.
- Local C++ validation passed: **16/16 CTest tests**. PR CI was green across **22/22 checks**.
- `docker compose build engine` completed successfully and produced image `sha256:bfdb714219c324b306e568e92ad21351dee9e83c0f7fa92313251eab4207bb8e`.
- The existing production container `trading-engine-engine-1` remains stopped with exit code **137** and still references the older image `sha256:d0f58d6e48db1cb1442a308b7ab845a33d6532075ec30f3d1b3b25a92996d5d5`. The build did not replace or start that container; the cause of exit 137 has not been established.
- The production `risk-state.snapshot` and `trades.log` match the verified backup byte-for-byte. The backup manifest passes SHA-256 verification.
- A disposable recovery probe using a copy of the persisted state exited cleanly (**exit 0**) and logged the persisted `max_drawdown` halt with journal sequence 18. This is isolated recovery evidence, not proof of live-stack trade delivery, PostgreSQL persistence, or browser recovery.
- **Safety boundary:** production remains stopped; no production container replacement/start, risk-state reset, risk-limit change, or halt-resume action was performed. Preserve the active halt and persisted files during the remaining recovery work.

### Remaining Phase 5.14 exit criteria

- [ ] Demonstrate a fresh trade and corresponding analytics/risk event through the running Compose stack, with observable downstream delivery.
- [x] Verify browser-level WebSocket disconnect/reconnect and subscription restoration against the running stack.
  Evidence: `dashboard-react/e2e/websocket-recovery.e2e.ts` via `bun run test:e2e` against the running Compose stack, 2026-10-21: 1 test passed in 2.5s (real Chromium, real gateway WebSocket).
- [ ] Record the resulting evidence and confirm the final dashboard/browser acceptance checks.

**Note on remaining criteria:** The two remaining Phase 5.14 criteria (fresh trade + PostgreSQL persistence) are currently **not blocked by missing engine capability** — the engine generates trades correctly, as demonstrated by the 2026-10-22 scratch-engine run that produced 17 trades and self-halted. They are blocked by the gateway-side engine reconnect gap documented under Phase 4.7's Known Issue. A corrected B2 test (scratch engine with `--network-alias engine` + explicit gateway restart before and after the test window) would close both criteria once the reconnect behavior is understood.

- **Risk-state recovery incident (2026-10-16 → 2026-10-18):** diagnosed and closed. The pre-`96d6867` snapshot durability gap produced a NUL snapshot that persisted for ~2 days and caused repeated fail-closed startup; the current running image contains `96d6867`. See `docs/incident-2026-10-16-risk-snapshot-nul.md`. This resolves the "Local runtime risk-state recovery remains unverified" note in `CHANGELOG.md` but does not close the Phase 5.14 exit criteria (live trade delivery, browser reconnect, and dependency-failure recovery remain outstanding).

Optional URL overrides:

```bash
GATEWAY_URL=http://127.0.0.1:8080 \
DASHBOARD_URL=http://127.0.0.1:5173 \
ANALYTICS_METRICS_URL=http://127.0.0.1:9101/metrics \
bash scripts/validate-runtime.sh
```

This script is deliberately non-destructive: it does not start or stop containers, generate orders, reset risk state, or change persisted data. A passing smoke check verifies reachability and basic response contracts only. It does **not** replace the full live TRADE/ANALYTICS_UPDATE/RISK_EVENT, PostgreSQL persistence, disconnect/reconnect, and browser recovery checks below. Those checks must be run and recorded separately; never claim runtime validation solely from a successful build or passive health check.

### Analytics TCP-client disconnect/reconnect regression test

Run from `gateway-node/`:

```bash
bun test tests/analytics-client.test.ts
```

The recovery case forces the first isolated Analytics TCP connection to close, verifies a subsequent trade is buffered while disconnected, and checks that the queued frame is delivered after the client reconnects. This is deterministic service-level coverage merged in PR #140; it does not establish browser reconnect behavior, PostgreSQL persistence, or recovery of the full Docker Compose runtime.

### Deterministic gateway event-path contract test

Run from `gateway-node/`:

```bash
bun test tests/full-stack.integration.test.ts
```

This test uses isolated fake Engine and Analytics TCP servers plus a local Gateway instance. It verifies deterministic `TRADE`, `ANALYTICS_UPDATE`, and `RISK_EVENT` WebSocket delivery, then checks that the market, recent-trades, and analytics REST snapshots reflect those fixtures. It does not start Docker Compose, connect to PostgreSQL, mutate live persisted risk state, or prove real runtime persistence/reconnect behavior. Treat it as contract coverage, not a substitute for the end-to-end exit criteria.

### Validation sequence

The smoke script is a passive preflight, not the full integration acceptance test. Record the live-event, persistence, and recovery evidence below separately. Do not mark Phase 5.14 complete based on smoke-check output alone.

```text
1. Start PostgreSQL.
2. Start Python Analytics.
3. Start C++ Trading Engine.
4. Start Gateway.
5. Start React Dashboard.
6. Open the dashboard.
7. Verify REST snapshots.
8. Verify WebSocket connection.
9. Verify the independent MARKET_DATA path while observing the current risk state.
10. When a real trade can be generated safely under the configured risk controls, verify TRADE reaches the dashboard.
11. Verify analytics update reaches the dashboard.
12. Verify risk update/event reaches the dashboard when generated.
13. Verify trade/analytics persistence in PostgreSQL.
14. Stop/restart a dependency.
15. Verify dashboard stale/disconnected state.
16. Restore dependency.
17. Verify automatic recovery.
```

### Required end-to-end path

```text
C++ Engine
   ↓ TRADE
Gateway
   ├──→ WebSocket → React Dashboard
   └──→ Analytics TCP
              ↓
       Python Analytics
              ↓
          PostgreSQL
              ↓
       Analytics output
              ↓
          Gateway
              ↓
       WebSocket
              ↓
       React Dashboard
```

### Exit criteria

- [ ] Real engine trade reaches React.
- [ ] Real analytics result reaches React.
- [ ] Real risk event reaches React when generated.
- [ ] PostgreSQL persistence is verified.
- [ ] WebSocket reconnect/recovery works.
- [ ] Dependency failure states are visible.
- [ ] Recovery returns the dashboard to live state.
- [ ] Runtime validation passes without bypassing Gateway.
- [X] Verify browser-level WebSocket disconnect/reconnect and subscription restoration against the running stack.
  Evidence: `dashboard-react/e2e/websocket-recovery.e2e.ts` via `bun run test:e2e` against the running Compose stack, 2026-10-21: 1 test passed in 2.5s (real Chromium, real gateway WebSocket).

---

## Phase 5.15 — Documentation, Cleanup & Phase Exit

**Status:** ⏳ Planned

Close Phase 5 only after implementation, tests, runtime validation, and documentation are aligned.

### Documentation

Update:

```text
docs/05-roadmap-and-phases.md
docs/17-changelog.md
README.md
```

Document:

- Dashboard architecture.
- Routes/pages.
- Gateway REST usage.
- WebSocket event usage.
- Environment variables.
- Local development startup.
- Runtime integration.
- Test commands.
- Known limitations.
- Production-readiness boundaries.

### Cleanup

- Remove dead frontend code.
- Remove unused dependencies.
- Remove temporary mock data used only during implementation.
- Resolve TypeScript/build warnings.
- Resolve browser console errors.
- Verify formatting/linting.
- Verify no hardcoded environment URLs.
- Verify no direct engine/analytics connections from React.

### Phase 5 exit checklist

- [ ] Dashboard foundation complete.
- [ ] REST client complete.
- [ ] WebSocket client complete.
- [ ] Reconnect/resubscribe complete.
- [ ] Dashboard navigation complete.
- [ ] Live market data complete.
- [ ] Recent trades complete.
- [ ] Order book complete.
- [ ] VWAP/SMA/EMA/volatility views complete.
- [ ] Portfolio/P&L complete.
- [ ] Risk state/events complete.
- [ ] Engine/analytics/system status complete.
- [ ] Loading/empty/error/stale states complete.
- [ ] Responsive UI complete.
- [ ] Accessibility baseline complete.
- [ ] Automated tests complete.
- [ ] Browser E2E complete.
- [ ] Full runtime validation complete.
- [ ] Documentation updated.
- [ ] Cleanup complete.
- [ ] CI passes.

**Phase 5 overall status:** 🚧 In Progress — implementation hardening through PR #140 is merged. Phase 5.14 runtime acceptance remains active because real runtime event delivery, persistence, browser recovery, and dependency-failure evidence are still outstanding.

### Recommended Phase 5 commit sequence

```text
feat(dashboard): establish React dashboard foundation
feat(dashboard): add Gateway REST client
feat(dashboard): add Gateway WebSocket client
feat(dashboard): add dashboard layout and navigation
feat(dashboard): add live market and trade views
feat(dashboard): add order book visualization
feat(dashboard): add analytics views
feat(dashboard): add portfolio and risk views
feat(dashboard): add system status views
feat(dashboard): add dashboard loading and error states
feat(dashboard): add responsive and accessible UI
test(dashboard): add frontend and browser validation
test(dashboard): validate full runtime integration
docs(dashboard): document Phase 5 and closeout
```

This sequence keeps each milestone independently reviewable and makes it possible to stop at any completed step without mixing dashboard UI work with backend contract changes.

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

| Phase | Component                                   | Status                                                                                             |
| ----- | ------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| 1     | C++ Order Book & Matching Engine            | ✅ Complete                                                                                        |
| 2     | C++ TCP Transport                           | ✅ Complete                                                                                        |
| 3.1   | Analytics Foundation                        | ✅ Complete                                                                                        |
| 3.2   | Domain Models                               | ✅ Complete                                                                                        |
| 3.3   | Technical Indicators                        | ✅ Complete                                                                                        |
| 3.4   | Socket Ingestion                            | ✅ Complete                                                                                        |
| 3.5   | Streaming Analytics                         | ✅ Complete                                                                                        |
| 3.6   | Risk Analytics                              | ✅ Complete                                                                                        |
| 3.7   | Risk Limits & Risk Events                   | ✅ Complete                                                                                        |
| 3.8   | PostgreSQL Persistence & Observability      | ✅ Complete                                                                                        |
| 3.9   | Metrics & Observability                     | ✅ Complete                                                                                        |
| 3.10  | Analytics Service Hardening                 | ✅ Complete                                                                                        |
| 4.1   | Gateway Foundation & Architecture           | ✅ Complete                                                                                        |
| 4.2   | Gateway Configuration & Runtime Hardening   | ✅ Complete                                                                                        |
| 4.3   | Gateway HTTP API                            | ✅ Complete                                                                                        |
| 4.4   | Engine Protocol & Event Normalization       | ✅ Complete                                                                                        |
| 4.5   | WebSocket Gateway                           | ✅ Complete                                                                                        |
| 4.6   | Python Analytics Integration                | ✅ Complete                                                                                        |
| 4.7   | Error Handling, Resilience & Backpressure   | ✅ Complete                                                                                        |
| 4.8   | Security Boundaries & Input Hardening       | ✅ Complete                                                                                        |
| 4.9   | Operational Logging & Metrics               | Complete                                                                                           |
| 4.10  | Testing & Integration Validation            | ✅ Complete                                                                                        |
| 4.11  | Phase Integration & Exit Criteria           | ✅ Complete                                                                                        |
| 5.0   | Dashboard Repository Inspection & Baseline  | ✅ Complete                                                                                        |
| 5.1   | Dashboard Foundation & Application Shell    | ✅ Complete                                                                                        |
| 5.2   | Gateway REST Client & Typed API Models      | ✅ Complete                                                                                        |
| 5.3   | WebSocket Client, Protocol & Reconnection   | ✅ Complete                                                                                        |
| 5.4   | Dashboard Layout & Navigation               | ✅ Complete                                                                                        |
| 5.5   | Live Market Data & Recent Trades            | ✅ Complete                                                                                        |
| 5.6   | Order Book Visualization                    | ✅ Complete                                                                                        |
| 5.7   | Analytics Charts & Indicator Views          | ✅ Complete                                                                                        |
| 5.8   | Portfolio, P&L & Risk Dashboard             | ✅ Complete                                                                                        |
| 5.9   | Engine, Analytics & System Status           | ✅ Implementation complete                                                                         |
| 5.10  | Loading, Error & Stale-Data UX              | ✅ Implementation complete — PR #120                                                              |
| 5.11  | Responsive UI & Dashboard Production Polish | ✅ Implementation complete for current scope                                                       |
| 5.12  | Halted-State Market Data                    | ✅ Complete — PR #132                                                                             |
| 5.13  | Data Integrity & Observability              | ✅ Complete — PRs #133 and #134                                                                   |
| 5.14  | Full Runtime Integration Validation         | 🚧 In Progress — isolated restart, gateway event, and browser reconnect tests pass; live-runtime event delivery and legacy halt diagnostics remain unverified/unavailable |
| 5     | React Dashboard                             | 🚧 In Progress                                                                                     |
| 6     | Historical Analytics                        | ⏳ Planned                                                                                         |
| 7     | Authentication & Security                   | ⏳ Planned                                                                                         |
| 8     | Platform Observability                      | ⏳ Planned                                                                                         |
| 9     | Deployment & Infrastructure                 | ⏳ Planned                                                                                         |
| 10    | Performance & Production Hardening          | ⏳ Planned                                                                                         |

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
