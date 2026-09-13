# ADR-007: Persistence Architecture

**Status:** Accepted

**Date:** 2026-09-13

**Phase:** Phase 3.8 — Persistence

---

## 1. Context

The Trading Engine currently processes market and trade events primarily in memory.

The Python analytics service consumes authoritative `TRADE` events from the C++ trading engine and maintains streaming state for:

* indicators,
* position,
* realized PnL,
* unrealized PnL,
* equity,
* peak equity,
* drawdown,
* risk limits,
* risk events.

This in-memory design is sufficient for the current streaming analytics implementation, but it does not provide durable state or historical queries.

Phase 3.8 introduces persistence for:

* trade events,
* analytics results,
* position state,
* risk state,
* historical analytics queries,
* database integration,
* database schema,
* persistence tests.

Persistence must be introduced without coupling the streaming analytics domain directly to a specific database implementation.

---

## 2. Decision

The analytics service will use a persistence abstraction based on repository interfaces.

The streaming analytics pipeline remains responsible for calculating domain state.

The persistence layer is responsible for storing and retrieving durable state.

The initial architecture is:

```text
C++ Trading Engine
        |
        | TRADE
        v
Python Analytics
        |
        v
StreamingProcessor
        |
        +-------------------+
        |                   |
        v                   v
AnalyticsResult        RiskEvent
        |                   |
        +---------+---------+
                  |
                  v
          Persistence Layer
                  |
          Repository Interfaces
                  |
                  v
          Database Adapter
                  |
                  v
              PostgreSQL
```

The database implementation must remain behind the persistence boundary.

---

## 3. Architectural Boundaries

### 3.1 Streaming Analytics

The `StreamingProcessor` owns in-memory streaming computation.

It is responsible for:

* consuming `Trade` events,
* maintaining per-symbol indicator state,
* maintaining risk state,
* calculating analytics,
* evaluating risk limits,
* generating risk events.

It must not:

* open database connections,
* execute SQL,
* depend directly on PostgreSQL,
* construct database-specific models.

The processor remains database-agnostic.

---

### 3.2 Persistence Layer

The persistence layer provides durable storage operations for analytics-domain data.

Conceptually:

```text
Domain
  |
  v
Repository Interfaces
  |
  v
Persistence Adapter
  |
  v
Database
```

The domain layer must depend on repository contracts rather than database-specific implementations.

---

## 4. Repository Responsibilities

The persistence design will use separate repository boundaries for different persisted concepts.

### 4.1 TradeRepository

Responsible for durable trade-event storage.

Conceptual operations:

```text
save(trade)
get_by_id(trade_id)
list_by_symbol(symbol)
list_by_time_range(start, end)
```

The repository must preserve the authoritative trade information received from the trading engine.

The trade event remains the source of truth for executed trades.

---

### 4.2 AnalyticsRepository

Responsible for persisted analytics results.

Conceptual operations:

```text
save(result)
get_by_event_id(event_id)
list_by_symbol(symbol)
list_by_time_range(start, end)
```

Analytics results are derived data.

They must not replace the authoritative trade history.

---

### 4.3 PositionRepository

Responsible for durable position state.

Conceptual operations:

```text
save(position_state)
get_by_symbol(symbol)
list_by_symbol(symbol)
```

Position state is derived from the processed trade stream and risk processing.

The repository stores the latest durable state needed for recovery and historical inspection.

---

### 4.4 RiskRepository

Responsible for durable risk state and risk events.

Conceptual operations:

```text
save_risk_state(risk_state)
save_event(risk_event)
get_latest_state(symbol)
list_events(symbol)
list_events_by_time_range(symbol, start, end)
```

Risk events are immutable historical records.

Risk state represents the latest recoverable state.

---

## 5. Persistence Direction

Persistence must consume domain results rather than become part of the calculation path.

The intended flow is:

```text
TRADE
  |
  v
StreamingProcessor
  |
  +----> AnalyticsResult
  |
  +----> RiskEvent
  |
  v
Persistence Boundary
  |
  +----> TradeRepository
  |
  +----> AnalyticsRepository
  |
  +----> PositionRepository
  |
  +----> RiskRepository
```

The first implementation may persist these results synchronously.

Asynchronous persistence, queues, batching, or event-log based persistence may be introduced later if required by performance measurements.

---

## 6. PostgreSQL Boundary

PostgreSQL is the planned initial durable database.

PostgreSQL-specific implementation must remain below the repository interfaces.

Conceptually:

```text
analytics/
├── domain/
│
├── pipeline/
│
├── persistence/
│   ├── repositories/
│   │   ├── trade.py
│   │   ├── analytics.py
│   │   ├── position.py
│   │   └── risk.py
│   │
│   └── postgres/
│       ├── trade.py
│       ├── analytics.py
│       ├── position.py
│       └── risk.py
```

The exact package structure may be refined during implementation.

This ADR defines the architectural boundary, not the final Python module layout.

---

## 7. Domain-to-Database Mapping

Domain models must not be replaced with database models.

The intended separation is:

```text
Domain Model
    |
    | mapping
    v
Persistence Model
    |
    v
Database Row
```

For example:

```text
Trade
  |
  v
TradeRecord
  |
  v
trades table
```

This prevents SQL/database concerns from leaking into domain models.

---

## 8. Trade Persistence

Trades are the primary historical input to analytics.

The persistence schema must retain sufficient information to reconstruct the original authoritative trade event.

At minimum, the persisted trade record must represent:

```text
event_id
event_type
trade_id
symbol
price
quantity
timestamp
taker_side
buy_order_id
sell_order_id
taker_order_id
maker_order_id
```

Optional fields may be stored as nullable database columns.

Prices and other monetary values must preserve decimal precision.

Floating-point storage must not be used for monetary values.

---

## 9. Analytics Persistence

An `AnalyticsResult` represents derived analytics for a processed trade.

The persistence model must retain the values necessary for historical analytics queries.

The persisted analytics record should represent:

```text
event_id
event_type
symbol
price
vwap
sma
ema
position
realized_pnl
unrealized_pnl
equity
peak_equity
drawdown
timestamp
```

Analytics records reference the processed event through identifiers and timestamps rather than replacing the original trade record.

---

## 10. Position Persistence

Position state is derived state.

The persistence design must distinguish between:

```text
Historical trade events
        |
        v
Derived position state
```

Trade history remains the authoritative source for replay or complete reconstruction.

Persisted position state exists primarily to support:

* recovery,
* current-state queries,
* operational inspection,
* faster startup.

The system must not assume that persisted position state is the only source from which a position can be reconstructed.

---

## 11. Risk Persistence

Risk persistence has two conceptual categories.

### Current risk state

Stores the latest state required for recovery and inspection.

Examples:

```text
position
equity
peak_equity
drawdown
risk-limit status
```

### Risk events

Stores immutable risk-limit events such as:

```text
RISK_LIMIT_WARNING
RISK_LIMIT_BREACHED
```

Risk events should retain:

```text
event_id
event_type
symbol
limit_type
status
threshold
warning_threshold
current_value
timestamp
```

Risk-event history must not be overwritten when a newer risk state is stored.

---

## 12. Historical Queries

Phase 3.8 must support historical analytics access through repository boundaries.

Initial query dimensions should include:

```text
symbol
event_id
time range
```

Example conceptual queries:

```text
Trades for SIM between T1 and T2

Analytics results for SIM between T1 and T2

Latest position for SIM

Latest risk state for SIM

Risk events for SIM between T1 and T2
```

Pagination and advanced filtering may be added when the query requirements are implemented.

---

## 13. Transaction Boundaries

A single processed trade may produce multiple persistence records:

```text
Trade
AnalyticsResult
PositionState
RiskEvent[]
```

The persistence implementation should provide a clear consistency boundary for related records.

The initial PostgreSQL implementation should prefer a transaction that keeps records generated from the same processed trade consistent.

If persistence fails, the failure must not silently appear as successful durable storage.

Error handling and retry behavior will be defined during the persistence implementation.

---

## 14. Failure and Recovery

Persistence failures must be distinguishable from analytics failures.

The system should be able to determine whether:

```text
Analytics processing succeeded
Persistence succeeded
Persistence failed
```

The initial implementation must not silently discard persistence errors.

Recovery mechanisms may later include:

* retry,
* write-ahead/event logging,
* replay,
* checkpointing,
* idempotent writes.

These are implementation concerns and are not all required in the first Phase 3.8 persistence implementation.

---

## 15. Idempotency

Persistence operations should be designed around stable event identifiers.

The primary identifiers are:

```text
trade_id
event_id
```

Duplicate delivery of the same event must not unintentionally create multiple logical copies of the same historical event.

Database constraints should enforce uniqueness where appropriate.

---

## 16. Schema Principles

The database schema should follow these principles:

1. Domain identifiers remain opaque.
2. Monetary values preserve decimal precision.
3. Timestamps use timezone-aware storage.
4. Required event fields are not nullable.
5. Historical event records are append-oriented.
6. Derived current-state tables may be updated.
7. Unique identifiers are enforced by database constraints.
8. Indexes support the initial historical query patterns.
9. Database-specific details remain outside domain models.

---

## 17. Migration Strategy

Database schema changes must be versioned.

Schema changes must not be applied manually as undocumented SQL changes.

The eventual persistence implementation will use a migration mechanism appropriate for the selected PostgreSQL access stack.

The migration tooling will be selected during implementation after the repository boundary has been established.

This ADR does not mandate a specific ORM or migration framework.

---

## 18. Database Dependency Policy

The current streaming analytics implementation must remain usable without PostgreSQL.

Therefore:

```text
Streaming analytics
        |
        +---- works without database
        |
        +---- persistence is optional infrastructure
```

PostgreSQL dependencies must not become mandatory for unit tests that exercise pure analytics-domain behavior.

Persistence-specific tests may require a database environment.

---

## 19. Testing Strategy

Persistence implementation will require multiple test layers.

### Unit tests

Test:

* repository contracts,
* domain-to-persistence mapping,
* validation,
* serialization,
* identifier handling.

### Integration tests

Test:

* PostgreSQL connection,
* schema creation,
* inserts,
* reads,
* transactions,
* uniqueness constraints,
* historical queries.

### Persistence failure tests

Test:

* connection failure,
* transaction failure,
* duplicate events,
* invalid records,
* rollback behavior.

### End-to-end tests

Verify:

```text
TRADE
  ↓
StreamingProcessor
  ↓
AnalyticsResult / RiskEvent
  ↓
Persistence
  ↓
Historical Query
```

Existing analytics unit tests must continue to pass without requiring PostgreSQL.

---

## 20. Performance Considerations

Persistence must not be allowed to silently redefine the latency characteristics of the streaming processor.

The initial implementation may use synchronous persistence for correctness and simplicity.

Performance optimization should be driven by measurements.

Potential future optimizations include:

* batching,
* asynchronous writes,
* connection pooling,
* prepared statements,
* partitioning,
* append-only event storage,
* background persistence workers.

These are not required by this ADR.

---

## 21. Alternatives Considered

### 21.1 Database calls directly from StreamingProcessor

Rejected.

Reasons:

* couples domain processing to infrastructure,
* complicates testing,
* makes database replacement difficult,
* mixes calculation and persistence responsibilities.

---

### 21.2 SQL statements directly inside domain models

Rejected.

Reasons:

* violates separation of concerns,
* introduces database dependencies into domain code,
* makes domain models difficult to reuse and test.

---

### 21.3 ORM-first architecture

Not selected as the architectural requirement.

An ORM may be used during implementation, but the repository boundary must remain independent of the ORM.

---

### 21.4 Event-log-only persistence

Deferred.

A replayable event log is valuable for recovery and deterministic reconstruction, but Phase 3.8 first requires durable trade, analytics, position, and risk persistence.

---

## 22. Resulting Architecture

The resulting Phase 3 architecture becomes:

```text
C++ Trading Engine
        |
        | TRADE
        v
Python Analytics
        |
        v
SocketClient
        |
        v
StreamingProcessor
        |
        +--------------------+
        |                    |
        v                    v
AnalyticsResult          RiskEvent
        |                    |
        +---------+----------+
                  |
                  v
          Persistence Layer
                  |
          +-------+-------+
          |       |       |
          v       v       v
       Trade  Analytics  Position
       Repo      Repo      Repo
                  |
                  v
             Risk Repo
                  |
                  v
              PostgreSQL
```

The persistence layer is an infrastructure boundary.

The streaming analytics domain remains independent of PostgreSQL.

---

## 23. Consequences

### Positive

* Database concerns remain isolated.
* Analytics can continue to run without PostgreSQL.
* Repository implementations can be tested independently.
* PostgreSQL can be replaced later.
* Historical queries have a defined architectural boundary.
* Durable state can be introduced incrementally.
* Existing Phase 3.1–3.7 functionality remains largely unchanged.

### Negative

* Additional repository abstractions are required.
* Domain-to-database mapping introduces additional code.
* Transactions and consistency require explicit handling.
* Integration tests require database infrastructure.

---

## 24. Phase 3.8 Implementation Boundary

This ADR defines the architecture only.

The following are intentionally **not implemented by this decision**:

* PostgreSQL connection code.
* ORM selection.
* Migration framework installation.
* SQL schema files.
* Repository implementations.
* Database Docker configuration.
* Historical query implementation.
* Persistence integration inside `StreamingProcessor`.

Those changes belong to subsequent Phase 3.8 implementation work.

---

## 25. Decision Summary

Phase 3.8 will introduce persistence behind repository interfaces.

The core rule is:

```text
StreamingProcessor calculates.
Persistence stores.
Repositories abstract storage.
PostgreSQL implements storage.
```

The analytics domain remains database-agnostic.

Trade history remains authoritative.

Analytics, position, and risk data are persisted as derived state or derived events.

Historical queries operate through persistence repositories rather than direct database access from the analytics pipeline.
