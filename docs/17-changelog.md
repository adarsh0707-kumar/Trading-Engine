## 2026-10-06 — Phase 5.8 — Portfolio, P&L & Risk Dashboard

### Status

**Status:** ✅ Complete

Phase 5.8 adds the live portfolio and risk dashboard using the existing Gateway analytics contract. No new backend contract or analytics calculation was introduced.

### Implemented

- Live position and mark-price display.
- Absolute portfolio exposure.
- Realized, unrealized, and total P&L.
- Current and peak equity.
- Absolute drawdown with percentage-from-peak presentation.
- Volatility and server-provided risk status.
- Live RISK_EVENT and analytics state updates through the existing WebSocket path.
- Loading, error, retry, refresh, and connection-state treatment.
- Responsive Portfolio & Risk layout.
- Explicit source-of-truth messaging: risk thresholds remain authoritative in Python Analytics/Gateway.

### Validation

```text
Docker Compose runtime          PASS — all services healthy
Gateway analytics endpoint      PASS — HTTP 200
Dashboard analytics proxy       PASS — HTTP 200
WebSocket                       PASS — OPEN
CI                              PASS — all checks
```

### Important correction

The Gateway analytics contract supplies **absolute monetary drawdown**. The dashboard now renders that value directly and derives a secondary percentage relative to peak equity. It no longer treats absolute drawdown as a fractional percentage.

### Scope boundary

Phase 5.8 is frontend-only. Gateway, Python Analytics, PostgreSQL, and engine contracts were not changed.

### Next Target

**Phase 5.9 — Engine, Analytics & System Status**

---

# Trading Engine — Changelog

## 2026-10-06 — Phase 5.9 Completion & Phase 5.10 Start

### Status

**Status:** Phase 5.9 complete; Phase 5.10 active

### Phase 5.9 — Engine, Analytics & System Status

Phase 5.9 added the dashboard's operational status view using the existing Gateway contracts.

### Implemented

* Live Gateway, Engine, and Analytics dependency status.
* Engine connection state.
* Engine connected-at timestamp.
* Last engine message timestamp.
* Last engine heartbeat timestamp.
* Engine reconnect-attempt count.
* Gateway /api/v1/status and /api/v1/status/engine consumption.
* Five-second status polling.
* Retry and inline error handling.
* System readiness/degraded presentation.
* Responsive system-status layout.
* Explicit source-of-truth messaging for engine telemetry.
* No Gateway, Python Analytics, PostgreSQL, or C++ Engine contract changes.

### Validation

Frontend production build: PASS
Frontend test suite: PASS — 12/12
CI: PASS
PR #119: MERGED

### Phase 5.10 — Loading, Empty, Error & Stale-Data UX

Phase 5.10 is now active. The milestone hardens the dashboard's live-data failure and freshness behavior across Market, Trades, Order Book, Analytics, Portfolio/Risk, System, and WebSocket flows.

### Planned focus

* Consistent loading, empty, error, stale, and disconnected states.
* Preserve last-known-good data during transient failures.
* Make data age/freshness visible instead of silently presenting old values as live.
* Expose WebSocket reconnecting/disconnected state without blanking valid data.
* Establish shared freshness semantics across dashboard hooks and pages.
* Keep user-facing errors concise and safe.
* Re-test build, frontend behavior, and performance after the UX changes.

### Next target

**Phase 5.10 — Loading, Empty, Error & Stale-Data UX**

---



All notable changes to the **Cloud-Based Algorithmic Trading Engine** are documented in this file.

The project follows a phased implementation roadmap covering:

* C++ matching engine
* C++ TCP transport
* Python streaming analytics
* Risk management
* Node.js gateway
* React dashboard
* Persistence
* Observability
* Infrastructure
* CI/CD and security
* Performance and production hardening

---

## 2026-10-04 — Phase 5 Dashboard Visual Design

### Status

**Status:** 🚧 Active design foundation

The React dashboard visual language is now defined and applied to the existing dashboard shell and overview page.

### Visual direction

**Liquid Glass + Bento Grid + Spatial Minimalism**

The dashboard uses layered glass panels, a bento-style information layout, restrained depth, and minimal visual noise.

### Exact three-color palette

The dashboard visual system is intentionally restricted to exactly three colors:

- Chocolate Brown: `#4E342E` — application background and dark surfaces.
- Cream: `#F8F4E7` — primary text and light contrast.
- Burnt Orange: `#CC5500` — brand accent, active states, actions, and highlights.

Only opacity variants of these same three colors are permitted for glass, borders, shadows, gradients, and depth. No blue, green, red, amber, gray, or other colors are part of the dashboard visual system.

### Status treatment

Semantic states reuse the three-color palette with explicit labels/icons instead of adding colors. BUY/PROFIT/healthy and RISK/WARNING/degraded use Burnt Orange; SELL/LOSS/error/breached use Chocolate Brown with structural emphasis; neutral/disconnected states use Cream at reduced opacity.

### Applied

- Redesigned the application background, grid texture, sidebar, header, and connection badge.
- Added cobalt active navigation treatment and restrained glass surfaces.
- Redesigned the Dashboard overview as a responsive bento grid.
- Kept live values empty until Gateway REST/WebSocket data is available.
- Centralized all visual tokens in `dashboard-react/src/styles/tokens.css`.
- Recorded the design contract in `docs/05-roadmap-and-phases.md`.

---

## 2026-10-04 — Phase 4.10 / 4.10.1 / 4.11 — Phase 4 Runtime & Integration Closeout

### Status

**Status:** ✅ Complete

Phase 4 is now closed. The completed Gateway platform was validated as a real multi-service backend runtime, and the Phase 4 integration exit criteria were recorded.

### Implemented and validated

* Real C++ Engine runtime container.
* Real Python Analytics runtime container.
* PostgreSQL runtime with initialized persistence schema.
* Gateway runtime container exposing REST and WebSocket boundaries.
* Real Engine TCP → Gateway → Analytics TCP → PostgreSQL → Gateway analytics-output path.
* Real WebSocket TRADE delivery from the running engine.
* Real WebSocket ANALYTICS_UPDATE delivery.
* PostgreSQL verification that a real Engine-generated trade is persisted.
* Runtime-stack readiness/startup validation.
* Docker Compose CI validation of the backend runtime.
* Gateway/Engine/Analytics disconnect and recovery behavior remains covered by service-level resilience suites.
* Phase 4 security regression and full Gateway validation.
* C++ Debug/Release and Python/PostgreSQL validation.
* Phase 4 documentation and exit evidence.

### Runtime path

    C++ Engine :9000
          ↓
    Gateway :8080
          ├── TCP → Python Analytics :8000
          │             ↓
          │        PostgreSQL :5432
          │
          └── analytics output
                 ↓
            WebSocket /ws

### Phase 4 exit criteria

* [X] Engine transport reachable from Gateway.
* [X] Real TRADE events forwarded to Python Analytics.
* [X] Real TRADE events processed by Python Analytics.
* [X] Analytics results persisted to PostgreSQL.
* [X] Analytics results returned to Gateway.
* [X] Live analytics published to WebSocket consumers.
* [X] Health/readiness and observability boundaries present.
* [X] Security regression and full Gateway suites pass.
* [X] C++ Debug/Release and Python/PostgreSQL suites pass.
* [X] Runtime stack validated in CI.
* [X] Phase 4 documentation and exit evidence recorded.

### Important scope boundary

This closes the **backend trading-platform integration**, not the complete end-user product. The React dashboard, historical analytics UI/API work, concrete authentication provider integration, production deployment, and performance/production hardening remain future milestones.

### Repository status after Phase 4 closeout

The current main branch is based on merged PR #95 / Phase 4.10.1 runtime integration.

The repository also contains legacy/empty CI workflow files — build.yml, docker.yml, lint.yml, and security.yml — whose workflow runs fail because they contain no jobs. These are repository-hygiene work items, not failures of the Phase 4 application/runtime implementation.

### Next target

**Phase 5 — React Dashboard**

---

All notable changes to the **Cloud-Based Algorithmic Trading Engine** are documented in this file.

The project follows a phased implementation roadmap covering:

* C++ matching engine
* C++ TCP transport
* Python streaming analytics
* Risk management
* Node.js gateway
* React dashboard
* Persistence
* Observability
* Infrastructure
* CI/CD and security
* Performance and production hardening

---

## 2026-09-29 — Phase 4 Planning — TypeScript Gateway on Bun

### Status

**Status:** ⏳ Planned

Phase 4 has been expanded into a detailed implementation plan before gateway development begins.

### Technology decisions

- TypeScript is the gateway implementation language.
- Bun is the gateway runtime and package manager.
- Bun test is the default gateway test runner.
- Fastify is the planned HTTP framework.
- ws is the planned WebSocket transport.
- Zod is the planned runtime validation layer.
- Pino is the planned operational logging library.
- Prometheus-compatible metrics are planned for gateway observability.
- The existing C++ engine protocol and JSON contracts remain the initial upstream contract.

### Planned sub-phases

- 4.1 Gateway foundation and architecture.
- 4.2 Configuration and environment management.
- 4.3 C++ engine TCP client.
- 4.4 Engine protocol and event normalization.
- 4.5 REST API.
- 4.6 WebSocket gateway.
- 4.7 Python analytics integration.
- 4.8 Error handling, resilience, and backpressure.
- 4.9 Security boundaries and input hardening.
- 4.10 Operational logging and metrics.
- 4.11 Testing and integration validation.
- 4.12 Phase integration and exit criteria.

The detailed scope, responsibilities, dependencies, failure cases, tests, and completion criteria are maintained in docs/05-roadmap-and-phases.md.

### Phase 4 planning outcome

The gateway will act as the application and client-transport boundary. It will not duplicate C++ matching logic or Python analytics calculations. The C++ engine remains authoritative for engine/trade state, while Python Analytics remains authoritative for analytics and risk state.

Bun is the standard gateway workflow for local development and CI; npm is not the default package manager for Phase 4.

---

## 2026-09-29 — Phase 3.10 — Analytics Service Hardening

### Status

**Status:** ✅ Complete

Phase 3.10 hardens the Python analytics service for reliable long-running operation across lifecycle management, configuration validation, resource cleanup, backpressure, failure recovery, and operational logging.

### 3.10.1 — Service Lifecycle Hardening ✅

Implemented:

* Idempotent service start and stop handling.
* Safe cleanup for startup and shutdown paths.
* Explicit trading-engine connection lifecycle handling.
* Lifecycle-focused regression coverage.

### 3.10.2 — Configuration Validation ✅

Implemented:

* Analytics service configuration validation.
* Engine host and port validation.
* Timeout and reconnection configuration validation.
* Payload-size validation.
* Risk configuration validation.
* Configuration-focused tests.

### 3.10.3 — Resource Cleanup ✅

Implemented:

* Deterministic socket cleanup.
* Publisher cleanup.
* Persistence resource cleanup.
* Repository lifecycle handling.
* Shutdown cleanup regression coverage.

### 3.10.4 — Backpressure Handling ✅

Implemented:

* Bounded analytics message queue.
* Configurable queue capacity.
* Rejection of inbound work when the queue is full.
* Backpressure state handling.
* Backpressure operational logging.
* Backpressure-focused tests.

### 3.10.5 — Failure Recovery ✅

Implemented:

* Bounded persistence retries.
* Persistence retry delays.
* Persistence failure propagation.
* Publisher retry handling.
* Engine disconnect recovery.
* Socket reconnect handling.
* Malformed-message recovery.
* Recovery-focused integration and unit tests.

Failed persistence transactions do not result in analytics publication.

### 3.10.6 — Operational Logging ✅

Implemented:

* Centralized logging configuration.
* Configurable log level and log format.
* Standardized service lifecycle logs.
* Engine connection and disconnection logs.
* Parser and backpressure failure logs.
* Persistence retry, success, and terminal-failure logs.
* Publisher retry and failure logs.
* Trade-processing failure logs.
* Operational logging configuration tests.

Supported environment configuration:

```text
TRADING_ENGINE_LOG_LEVEL
TRADING_ENGINE_LOG_FORMAT
```

### Phase 3.10 Validation

```text
Analytics Python test suite    PASS — 447 passed
GitHub Actions checks           PASS — 9/9
```

### Phase 3.10 Exit Criteria

* [X] Service lifecycle hardening.
* [X] Configuration validation.
* [X] Resource cleanup.
* [X] Backpressure handling.
* [X] Failure recovery.
* [X] Operational logging.
* [X] Recovery-focused tests.
* [X] Operational logging tests.
* [X] Full analytics test suite passing.
* [X] CI validation passing.

**Phase 3.10 overall status:** ✅ Complete

---

## 2026-09-28 — Phase 3.9 — Metrics and Observability

### Status

**Status:** ✅ Complete

Phase 3.9 expands observability from persistence-specific monitoring to service-wide operational metrics.

### Implemented

* Analytics service counters and processing duration metrics.
* Processing latency percentiles.
* Trade throughput metrics.
* Risk state and risk-event metrics.
* Error counters by category.
* Prometheus exposition and exporter lifecycle.
* Version-controlled Grafana dashboard provisioning.
* Service liveness and readiness state.
* Trading-engine connection health.
* Inbound message count and last-message timestamp.
* Automated tests for service health and Prometheus exposition.

### Service Health

Readiness is cleared when the trading-engine connection is lost or the service stops. Health state is exposed through Prometheus metrics for operational monitoring.

### Phase 3.9 Validation

- Service metrics: PASS
- Processing latency: PASS
- Trade throughput: PASS
- Risk metrics: PASS
- Error counters: PASS
- Prometheus integration: PASS
- Grafana dashboard: PASS
- Service health metrics: PASS

**Phase 3.9 exit status:** ✅ Complete

---

# 2026-10-03 — Phase 4.7 Completion & Phase 4.8 Start

**Status:** Phase 4.7 complete; Phase 4.8 active

Phase 4.7 is complete through the following milestones:

- 4.7.1 — Error Model & Failure Boundaries
- 4.7.2 — Engine Connection Resilience
- 4.7.3 — Engine Health & Liveness Monitoring
- 4.7.4 — Engine Liveness Failure & Recovery
- 4.7.5 — Analytics Backpressure & Graceful Degradation

Phase 4.8 — Security Boundaries & Input Hardening is now the active Gateway milestone.

### Phase 4.8 Scope

- External request and message input hardening.
- CORS policy hardening.
- Request and message size enforcement.
- Safe and deterministic error exposure.
- Rate-limit extension points.
- Authentication and authorization boundary preparation.
- Security-focused tests and validation.

---

# Status Legend

* ✅ Complete
* 🚧 In Progress
* ⏳ Planned
* ❌ Blocked

---

## 2026-09-28 — Phase 3.8 — PostgreSQL Persistence & Observability

### Status

**Status:** ✅ Complete

Phase 3.8 is complete. PostgreSQL persistence is implemented end-to-end for trades, analytics results, positions, risk state, and risk events, with repository contracts, application wiring, transaction boundaries, failure handling, observability, health checks, and migration lifecycle management.

### Implemented

* PostgreSQL connection configuration and connection factory.
* Repository contracts aligned with application interfaces.
* PostgreSQL analytics repository.
* PostgreSQL position repository.
* PostgreSQL risk repository.
* Shared PostgreSQL repository factory.
* Processed-trade persistence data-flow contract.
* Analytics-service persistence wiring.
* End-to-end PostgreSQL persistence coverage.
* Atomic persistence transaction boundary.
* Persistence failure handling with rollback and error propagation.
* Thread-safe persistence success/failure metrics.
* Persistence duration and failure logging.
* PostgreSQL health checks.
* Dedicated migration runner and bootstrap lifecycle.
* Deterministic migration discovery and ordering.
* Migration idempotency and duplicate-version validation.
* Atomic migration execution.
* Migration lifecycle integration tests.

### Persistence Flow

```text
TRADE
  ↓
Message Parser
  ↓
StreamingProcessor
  ├── Indicators
  └── Risk
  ↓
ProcessedTrade
  ↓
PostgreSQL Transaction
  ├── trades
  ├── analytics_results
  ├── positions
  ├── risk_state
  └── risk_events
  ↓
Commit
  ↓
AnalyticsPublisher
```

Publishing remains outside the database transaction, so a publish failure cannot create a second persistence transaction or partial database state.

### Migration Lifecycle

```text
Database URL
    ↓
PostgreSQL Connection
    ↓
MigrationRunner
    ├── discover migrations
    ├── validate versions
    ├── apply pending migrations
    └── record schema_migrations
    ↓
PostgresRepositories
    ↓
AnalyticsService
```

Migrations are executed only by the migration-aware bootstrap path. Injected repositories do not implicitly mutate database schema.

### PostgreSQL Schema

Migrations currently cover:

```text
001_create_trades.sql
002_create_analytics_results.sql
003_create_positions.sql
004_create_risk_state.sql
005_create_risk_events.sql
```

### Repository Layer

Implemented repositories:

* `PostgresAnalyticsRepository`
* `PostgresPositionRepository`
* `PostgresRiskRepository`

The repository factory exposes one shared PostgreSQL connection and a single lifecycle boundary for all repositories.

### Reliability & Observability

Phase 3.8 now includes:

* Transaction rollback on persistence failure.
* `PersistenceError` wrapping for unexpected persistence failures.
* No publication after a failed persistence transaction.
* Persistence success counters.
* Persistence failure counters.
* Total and average persistence duration.
* PostgreSQL dependency health checks.
* Structured persistence success/failure log context.
* Clean repository ownership and shutdown behavior.

### Validation

```text
Full analytics test suite        PASS — 312 passed
PostgreSQL E2E coverage          PASS — 2 passed
Migration lifecycle              PASS
Repository contract coverage     PASS
Persistence transaction coverage PASS
Failure-handling coverage        PASS
Observability/health coverage    PASS
```

### Phase 3.8 Exit Criteria

* [X] PostgreSQL connection configuration implemented.
* [X] Repository contracts aligned.
* [X] Trade persistence implemented.
* [X] Analytics-result persistence implemented.
* [X] Position-state persistence implemented.
* [X] Risk-state persistence implemented.
* [X] Risk-event persistence implemented.
* [X] Shared repository factory implemented.
* [X] Application persistence wiring implemented.
* [X] End-to-end PostgreSQL persistence validated.
* [X] Atomic transaction boundary implemented.
* [X] Persistence failure handling implemented.
* [X] Persistence observability implemented.
* [X] PostgreSQL health checks implemented.
* [X] Migration lifecycle implemented.
* [X] Full analytics test suite passing.

**Phase 3.8 overall status:** ✅ Complete

---

## 2026-09-13 — Phase 3.7 — Risk Management & Risk Events

**Status:** ✅ Complete

Phase 3.7 extends the Python analytics service with configurable risk limits, risk-limit evaluation, risk-event generation, and integration of risk events into the streaming trade-processing pipeline.

### 3.7.1 — Risk-Limit Configuration ✅

Implemented configurable risk-limit thresholds for the analytics risk layer.

#### Added

* `RiskLimitConfig` configuration model.
* Maximum position limit.
* Maximum position-value limit.
* Maximum drawdown limit.
* Maximum daily-loss limit.
* Configurable warning ratio.
* Validation for positive monetary and position limits.
* Validation ensuring the warning ratio remains between `0` and `1`.
* `Decimal`-based monetary configuration to avoid floating-point precision issues.

#### Configuration

Supported limits:

* `max_position`
* `max_position_value`
* `max_drawdown`
* `max_daily_loss`
* `warning_ratio`

---

### 3.7.2 — Risk-Limit Evaluation ✅

Implemented evaluation of configured risk limits against the current `RiskSnapshot`.

#### Added

* `RiskLimitType`
* `RiskLimitStatus`
* `RiskLimit`
* `RiskLimitState`
* `RiskLimitEvaluator`

#### Supported statuses

* `OK`
* `WARNING`
* `BREACHED`

#### Evaluation

The evaluator calculates risk states for:

* Maximum position.
* Maximum position value.
* Maximum drawdown.
* Maximum daily loss.

Warning thresholds are derived from the configured warning ratio.

Position value is calculated using the current market price and absolute position.

---

### 3.7.3 — Risk Events ✅

Implemented immutable risk-event models and event generation.

#### Added

* `RiskEvent`
* `RiskEventType`
* `RiskEventGenerator`

#### Supported events

* `RISK_LIMIT_WARNING`
* `RISK_LIMIT_BREACHED`

#### Event properties

Each generated event contains:

* Event ID.
* Event type.
* Symbol.
* Risk-limit type.
* Current status.
* Configured threshold.
* Warning threshold.
* Current value.
* Trade timestamp.

Risk-event IDs use symbol-scoped prefixes to keep generated events identifiable within per-symbol processing.

`OK` risk states do not generate events.

---

### 3.7.4 — Risk Event Integration ✅ Complete

Integrated risk-limit evaluation and risk-event generation into `StreamingProcessor`.

#### Added

* `ProcessedTrade` immutable result model.
* `process_trade_with_risk_events()` API.
* Per-symbol risk state.
* Per-symbol `RiskLimitEvaluator`.
* Per-symbol `RiskEventGenerator`.
* Risk-limit evaluation after each processed trade.
* Risk-event generation using the originating trade timestamp.

#### API compatibility

The existing:

```python
process_trade(trade) -> AnalyticsResult
```

API remains unchanged.

Internally, `process_trade()` delegates to:

```python
process_trade_with_risk_events(trade)
```

and returns only the `AnalyticsResult`.

The new API returns:

```text
ProcessedTrade
├── analytics
└── risk_events
```

When risk limits are not configured, `risk_events` is returned as an empty tuple.

#### Scope

Phase 3.7 intentionally does **not** include:

* Daily-loss tracking implementation.
* `AnalyticsPublisher` changes.
* Node.js/WebSocket integration.
* Changes to `AnalyticsResult.event_type`.
* Dashboard risk-event visualization.

These are reserved for later phases.

### Validation

Phase 3.7 implementation was validated with the Python analytics test suite.

Current validation target:

```text
173 tests passed
```

Additional processor-level validation:

```text
9 processor tests passed
```

`git diff --check` also passed during implementation.

### Phase 3.7 Exit Criteria

* [X] Risk-limit configuration implemented.
* [X] Risk-limit evaluation implemented.
* [X] Risk-event models implemented.
* [X] Risk-event generation implemented.
* [X] Streaming processor integration implemented.
* [X] Existing `process_trade()` API preserved.
* [X] Per-symbol risk state maintained.
* [X] Risk events returned separately from `AnalyticsResult`.
* [X] Existing analytics tests pass locally.
* **Phase 3.7 overall status:** ✅ Complete

---

## 2026-09-13 — Phase 3.7.3 Risk Events

**Status:** ✅ Complete

Phase 3.7.3 adds the risk-event domain and generation layer to the Python analytics service.

### Implemented

* Added `RiskEventType` for risk-limit warnings and breaches.
* Added immutable `RiskEvent` domain model.
* Added `RiskEvent.from_state()` conversion from `RiskLimitState`.
* Added JSON-friendly `RiskEvent.to_dict()` serialization.
* Added `RiskEventGenerator`.
* Added deterministic sequential risk-event identifiers.
* Added configurable event-ID prefixes.
* Added filtering of `OK` risk-limit states.
* Added warning-event generation.
* Added breach-event generation.
* Added Decimal serialization as strings.
* Added ISO-8601 timestamp serialization.
* Added validation for event state consistency.
* Added unit tests for risk-event generation and serialization.

### Risk Event Types

```text
RISK_LIMIT_WARNING
RISK_LIMIT_BREACHED

---

# Latest Commit Summary

## 2026-09-12 — Phase 3.6 Risk Analytics

**Status:** ✅ Complete

Phase 3.6 adds portfolio-risk state and P&L tracking to the Python streaming analytics pipeline.

### Implemented

* Added realized P&L calculation.
* Added unrealized P&L calculation.
* Added position tracking.
* Added average entry-price tracking.
* Added long-position handling.
* Added short-position handling.
* Added position reduction handling.
* Added position reversal handling.
* Added position-value calculation.
* Added equity tracking.
* Added peak-equity tracking.
* Added drawdown calculation.
* Added `RiskManager`.
* Added immutable `RiskSnapshot`.
* Added per-symbol risk state.
* Integrated risk state into `StreamingProcessor`.
* Integrated risk values into `AnalyticsResult`.
* Exported the risk API through `analytics.risk`.
* Added unit tests for P&L calculations.
* Added drawdown tests.
* Added position-sizing tests.
* Added risk-manager tests.
* Added processor-level risk integration tests.

### Risk State

Risk state is maintained independently for each symbol.

```text
Symbol
  ↓
Position
  ↓
Average Entry Price
  ↓
Realized P&L
  ↓
Unrealized P&L
  ↓
Equity
  ↓
Peak Equity
  ↓
Drawdown
```

### Analytics Result

The published `AnalyticsResult` now contains:

```text
event_id
event_type
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
timestamp
```

### Monetary Precision

Risk calculations use Python `Decimal` values for deterministic monetary calculations and to avoid floating-point rounding issues.

### Validation

```text
Python test suite       PASS — 144 passed
TRADE parsing           PASS
Socket ingestion        PASS
Risk integration        PASS
Per-symbol state        PASS
P&L calculations        PASS
Drawdown calculations   PASS
AnalyticsResult         PASS
```

### Result

Phase 3.6 completes the first portfolio-risk foundation for the analytics service.

```text
TRADE
  ↓
Trade
  ↓
StreamingProcessor
  ↓
Indicators
  +
RiskManager
  ↓
AnalyticsResult
  ↓
AnalyticsPublisher
```

### Next Target

**Phase 3.7 — Risk Limits and Risk Events**

---

# Historical Commit Summary

## 2026-09-12 — Phase 3.5 Streaming Analytics

**Status:** ✅ Complete

Phase 3.5 established the complete Python streaming analytics vertical slice from incoming C++ `TRADE` messages to deterministic analytics-result publication.

### Implemented

* Added per-symbol streaming state.
* Added incremental trade processing.
* Added incremental SMA calculation.
* Added incremental EMA calculation.
* Added incremental VWAP calculation.
* Added streaming volatility calculation.
* Added deterministic `AnalyticsResult` generation.
* Preserved source trade timestamps.
* Added unique analytics event identifiers.
* Added transport-independent `AnalyticsPublisher`.
* Added injectable callable publisher sinks.
* Added deterministic compact JSON serialization.
* Added stable JSON key ordering.
* Added `AnalyticsService` orchestration.
* Added end-to-end `TRADE → analytics-result` processing.
* Added regression coverage for the streaming pipeline.
* Exported analytics configuration through `analytics.config`.

### Streaming Pipeline

```text
C++ Trading Engine
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
Per-Symbol Analytics State
        ↓
SMA / EMA / VWAP / Volatility
        ↓
AnalyticsResult
        ↓
AnalyticsPublisher
        ↓
Deterministic JSON Output
```

### Analytics State

The processor maintains independent state for each symbol:

```text
SMA
EMA
VWAP
Volatility
```

### Publisher

`AnalyticsPublisher` separates analytics calculation from result delivery.

It supports:

* Injected callable sinks
* Deterministic JSON serialization
* Compact JSON output
* Stable key ordering
* Unique analytics event identifiers
* Transport-independent publication

This keeps the analytics processor independent from future downstream transports such as the Node.js gateway.

### Service Orchestration

```text
SocketClient
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
```

### Risk Fields at This Stage

The following fields existed in the result schema but remained deterministic placeholders during Phase 3.5:

```text
position = 0
realized_pnl = 0
unrealized_pnl = 0
equity = 0
peak_equity = 0
drawdown = 0
```

They were subsequently implemented in **Phase 3.6 — Risk Analytics**.

### Validation

```text
Full Python test suite       PASS — 92 passed
Publisher tests              PASS — 6 passed
End-to-end pipeline          PASS
TRADE parsing                PASS
Streaming processing         PASS
Indicator updates            PASS
AnalyticsResult generation  PASS
Publisher serialization      PASS
Deterministic JSON           PASS
```

---

## 2026-09-11 — TRADE Protocol Side and Order-ID Correction

**Status:** ✅ Complete

The original TRADE payload exposed taker and maker order identifiers but did not explicitly preserve the execution side.

Because taker/maker identity alone does not determine whether the taker bought or sold, the protocol was extended with explicit side information.

### Implemented

C++ TRADE payload now includes:

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

Python TRADE parsing now:

* Requires `taker_side`.
* Validates `taker_side`.
* Rejects unknown side values.
* Derives buy/sell order identifiers correctly.
* Preserves taker/maker relationships.

Python `Trade` now stores:

```text
taker_side
buy_order_id
sell_order_id
taker_order_id
maker_order_id
```

### Key Components

```text
engine-cpp/include/orderbook/Trade.hpp
engine-cpp/src/orderbook/Trade.cpp
engine-cpp/src/matching/MatchingEngine.cpp
engine-cpp/src/engine/Engine.cpp
engine-cpp/tests/unit/test_matching_engine.cpp

analytics-py/src/analytics/models/trade.py
analytics-py/src/analytics/ingestion/message_parser.py
analytics-py/src/analytics/pipeline/processor.py
```

Documentation was also updated to reflect the corrected trade-data model.

### Validation

```text
C++ Release tests    PASS — 15/15
Python tests          PASS — 89 passed
```

---

## 2026-09-11 — Unique Trade Identifiers

**Status:** ✅ Complete

The matching engine previously derived trade identifiers only from taker and maker order identifiers.

### Implemented

* Added a per-engine monotonic trade sequence.
* Changed trade identifiers to:

```text
trade-<sequence>-<taker>-<maker>
```

* Added tests covering repeated matches.

### Validation

```text
C++ Release tests    PASS — 15/15
C++ Debug tests      PASS — 15/15
```

---

## 2026-09-11 — Engine Shutdown and Robustness Fixes

**Status:** ✅ Complete

Several robustness issues were identified during C++ engine review and CI integration.

### Implemented

* Added `tests/TestCheck.hpp` so assertions remain active under `NDEBUG`.
* Fixed socket descriptor lifetime during receive and accept operations.
* Replaced heartbeat `sleep_for` shutdown waiting with a condition variable.
* Prevented rejected orders from terminating the engine process.
* Added GitHub Actions CI.
* Added Debug C++ test jobs.
* Added Release C++ test jobs.
* Added Python analytics test jobs.

### Key Files

```text
.github/workflows/test.yml

engine-cpp/include/network/SocketServer.hpp
engine-cpp/src/engine/Engine.cpp
engine-cpp/src/network/ClientConnection.cpp
engine-cpp/src/network/SocketServer.cpp

engine-cpp/tests/TestCheck.hpp
```

### Validation

```text
C++ Release tests    PASS — 15/15
C++ Debug tests      PASS — 15/15
Python test suite    PASS — 66 passed
GitHub Actions CI    PASS — 7/7 checks
```

---
