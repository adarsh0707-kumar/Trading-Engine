# Changelog

All notable changes to the Cloud-Based Algorithmic Trading Engine are documented here.

This project is an educational trading-infrastructure simulation. It does not connect to a real exchange or execute real financial transactions.

## [Unreleased]

### Phase 4.10 — Testing & Integration Validation

- Started the Phase 4.10 integration-validation milestone.
- Added a dedicated Gateway full-stack integration test covering Engine TRADE ingress, Analytics TCP forwarding, analytics output normalization, and WebSocket delivery.
- Added a dedicated `bun run test:integration` CI gate while retaining the existing service-level regression suites.
- Documented the remaining full-stack C++ Engine + Python Analytics + PostgreSQL validation required before Phase 4 exit.

Status: In Progress

### Phase 4.9.3 — Request & Event Correlation

- Propagated stable requestId and eventId correlation fields through Gateway engine, analytics, and WebSocket event boundaries.
- Preserved analytics requestId values when publishing ANALYTICS_UPDATE and RISK_EVENT events to WebSocket consumers.
- Added structured operational logs for accepted analytics outputs with both eventId and requestId.
- Kept HTTP request IDs and asynchronous dependency event IDs separate; no synthetic correlation IDs are created when an upstream request context is unavailable.
- Kept requestId/eventId out of Prometheus metric labels to preserve low-cardinality metrics.

Status: Complete

### Phase 4.9.2 — Metrics Completion

- Completed Gateway Prometheus metric coverage across HTTP, Engine, Analytics, WebSocket, and rate-limit boundaries.
- Added bounded HTTP request counters and duration histograms using low-cardinality method/status labels.
- Added Engine trade, Analytics lifecycle/output/error, WebSocket lifecycle/queue/heartbeat, and published-event metrics.
- Preserved existing Engine liveness/failure metrics and timestamp gauges while standardizing connection gauges.
- Added focused regression coverage for metric values, labels, units, and default connection state.
- No request IDs, event IDs, raw paths, client addresses, or payload contents are used as metric labels.

Status: Complete

### Phase 4.9.1 — Structured Operational Logging

- Added a shared structured Gateway operational logger with canonical service, component, event, outcome, requestId, eventId, and state fields.
- Standardized HTTP request lifecycle logging and Gateway startup/shutdown events.
- Standardized Engine and Analytics dependency lifecycle/failure logging without changing the public error contract.
- Added WebSocket connection, subscription, queue-overflow, and heartbeat-timeout operational events without logging client payload contents.
- Added regression coverage for the canonical operational log shape.

Status: Complete

## Phase 4.9 — Operational Logging & Metrics
- Phase 4.9 is the next active Gateway milestone after completion of the Phase 4.8 security hardening gate.
- Scope begins with structured operational logging, metric consistency, request/event correlation, and dependency observability across HTTP, engine, analytics, and WebSocket boundaries.
- Existing security boundaries remain unchanged while observability is extended.

### Phase 4.8 — Security Boundaries & Input Hardening
### Phase 4.8.7 — Security Regression & Integration Validation
- Added a dedicated Gateway security regression command covering Phase 4.8.1–4.8.6 boundaries.
- Added CI coverage for the Gateway Bun build, security regression suite, and full Gateway test suite.
- Kept the final Phase 4.8 gate validation-focused: no new authentication provider, credential verifier, or security feature is introduced.
- Updated the security milestone status to complete after the regression gate passes.
- Final Gateway validation completed with 182 tests passing and 0 failures.

### Phase 4.8.6 — AuthN/AuthZ Boundary Preparation
- Added explicit authentication state and principal types without introducing a credential verifier.
- Added reusable authentication and role/scope authorization guards for future protected routes.
- Added an injectable authentication resolver seam at the Gateway server boundary.
- Added opt-in authentication enforcement configuration; enforcement remains disabled by default.
- Preserved sanitized public 401/403 error handling and added regression coverage.

### Phase 4.8.5 — Rate-Limit Boundary
- Added a bounded in-process HTTP rate limiter with per-client fixed-window buckets.
- Added configurable request limits, windows, retained-client bounds, and an enable/disable switch.
- Added a stable HTTP 429 RATE_LIMITED error contract with sanitized messaging and Retry-After.
- Excluded health and Prometheus endpoints from the application rate-limit boundary.
- Added a Prometheus rejection counter and structured rejection logging.
- Added configuration, limiter, public-error, endpoint, and metrics regression coverage.

### Phase 4.8.4 — Safe Error Exposure / Public Error Contract
- Sanitized Gateway API error messages so internal exception details are never returned to clients.
- Added stable public messages for authentication, authorization, validation, not-found, conflict, dependency, and internal error classes.
- Preserved request IDs for client-side correlation without exposing framework or dependency internals.
- Added regression coverage for all public error codes, unexpected exceptions, and not-found responses.

### Phase 4.8.3 — CORS Security Hardening
- Replaced the single runtime CORS origin with a strict exact-origin allowlist.
- Added comma-separated `CORS_ORIGINS` configuration while preserving the existing `CORS_ORIGIN` setting for compatibility.
- Rejected wildcard, `null`, credential-bearing, path-bearing, malformed, duplicate, and empty CORS origins.
- Disabled credentialed CORS responses explicitly.
- Added configuration and runtime regression coverage for allowed, denied, and preflight requests.

### Phase 4.8.2 — HTTP/WebSocket Request Size & Boundary Enforcement
- Centralized the Gateway's 1 MiB transport payload ceiling for HTTP and WebSocket configuration.
- Prevented HTTP and WebSocket environment overrides from raising the configured payload boundary above 1 MiB.
- Enforced the configured WebSocket message size in the hub in addition to the underlying WebSocket transport limit.
- Mapped Fastify oversized HTTP request bodies to an explicit HTTP 413 response without exposing internal parser details.
- Added regression coverage for default limits, smaller limits, oversized configuration, WebSocket 1009 closure, and HTTP 413 handling.

### Phase 4.8.1 — External Input Validation & Payload Hardening
- Added shared validation primitives for strict object shapes, bounded strings, UTC timestamps, and bounded unique arrays.
- Hardened engine message envelopes against unexpected fields, malformed timestamps, oversized request IDs, and oversized payload fields.
- Hardened WebSocket subscription messages against unexpected fields, duplicate event subscriptions, and oversized event lists.
- Preserved the existing 1 MiB transport boundary while adding field-level validation before downstream normalization.
- Added focused security-boundary regression coverage for engine and WebSocket inputs.

- Established the Phase 4.8 security/input-hardening milestone as the next Gateway development target.
- Phase 4.7 resilience milestones 4.7.1–4.7.5 are complete and integrated on `main`.
- Phase 4.8 scope covers external-input validation, CORS hardening, request/message size enforcement, safe error exposure, rate-limit extension points, and future authentication/authorization boundaries.

### Phase 4.7.5 — Analytics Backpressure & Graceful Degradation
- Classified analytics outbound queue saturation with the shared Phase 4.7 `queue_overflow` failure type.
- Preserved the Gateway engine/WebSocket path when analytics is unavailable or its bounded outbound queue is full.
- Added a dedicated analytics queue-overflow health event and Prometheus counter.
- Added focused queue-overflow failure classification and metrics coverage.

### Phase 4.7.4 — Engine Liveness Failure & Recovery
- Added configurable engine heartbeat liveness timeout detection.
- Reset the liveness deadline after every valid engine HEARTBEAT.
- Classified stale-heartbeat failures as timeout failures and routed them through the existing reconnect lifecycle.
- Added a dedicated Prometheus liveness-failure counter.
- Preserved engine health timestamps and reconnect state for operational visibility.

### Phase 4.7.1 — Error Model & Failure Boundaries
- Added a stable failure taxonomy for connection, timeout, protocol, validation, queue overflow, dependency unavailability, processing, and shutdown failures.
- Added explicit recoverability semantics without changing existing reconnect or backpressure runtime behavior.
- Added Python analytics integration failure types and tests.
- Added Gateway failure types, classification, and tests.
- Added the Phase 4.7 resilience error-model documentation and failure-boundary policy.

### Phase 4.6.4 — Analytics Output Back to Gateway
- Extended the versioned analytics protocol with ANALYTICS_UPDATE and RISK_EVENT output envelopes.
- Made the existing Gateway ↔ Python analytics TCP connection bidirectional.
- Added fragmented and multiple-frame output decoding on the Gateway.
- Added Python-side framing and outbound Gateway publishing through the active receiver connection.
- Routed AnalyticsResult and generated RiskEvent objects back to the Gateway without duplicating analytics calculations.
- Added a Gateway-owned latest analytics snapshot for GET /api/v1/analytics.
- Added live analytics and risk-event WebSocket events.
- Connected analytics and engine connection state to the Gateway status endpoint.
- Added contract, transport, provider, and output serialization tests.

### Phase 4.6.3 — Python Analytics Receiver
- Added a Gateway-facing Python TCP receiver on the analytics service.
- Reused the existing 4-byte big-endian length-prefixed transport and 1 MiB payload limit.
- Added fragmented-frame, multiple-frame, UTF-8, disconnect, and reconnect handling.
- Routed complete Gateway payloads into the existing analytics service backpressure and processing pipeline.
- Reused the Phase 4.6.1 GatewayTradeMessage contract and existing MessageParser/Trade domain model without duplicating business parsing.
- Added receiver transport and configuration test coverage.

### Phase 4.6.2 — Gateway Analytics Client
- Added a dedicated Gateway TCP analytics client using the existing 4-byte length-prefixed transport.
- Forwarded normalized engine TRADE events using the versioned Phase 4.6.1 analytics contract.
- Added bounded outbound queuing while analytics is disconnected.
- Added exponential reconnect, connection timeout handling, lifecycle logging, and graceful shutdown.
- Added analytics transport configuration and client integration tests.

### Phase 4.6.1 — Gateway ↔ Python Analytics Contract
- Added versioned Gateway-to-analytics message contract definitions.
- Added typed Gateway TRADE envelope validation for event identity, timestamps, price, quantity, order identity, and taker side.
- Preserved the existing Python analytics transport representation: the TRADE payload remains a nested JSON string.
- Added Python-side contract validation that reuses the existing MessageParser and Trade domain model rather than duplicating analytics parsing rules.
- Added cross-service contract tests for valid TRADE messages and malformed envelopes/payloads.
- No runtime socket integration was changed in this sub-phase; the contract is the boundary for Phase 4.6.2.

## [2026-10-02]

### Phase 4.5 — WebSocket Gateway
- Added a configurable browser-facing WebSocket endpoint.
- Added connection lifecycle management and explicit subscribe/unsubscribe handling.
- Added typed TRADE event serialization using the Phase 4.4 normalized event model.
- Added server heartbeat/ping-pong and dead-client cleanup.
- Added bounded per-client outbound queues and slow-consumer protection.
- Added graceful WebSocket shutdown handling.
- Added unit and end-to-end coverage for live TRADE delivery from a fake TCP engine through the gateway WebSocket path.
- Added the gateway TCP engine event client using the existing 4-byte length-prefixed protocol.
- Connected normalized live TRADE events from the C++ engine to the WebSocket hub.
- Added engine HEARTBEAT handling with protocol-compliant HEARTBEAT/OK responses.
- Added bounded exponential reconnect, connection timeout handling, and engine connection lifecycle logging.
- Updated C++ HELLO/HEARTBEAT messages with request IDs and timestamps required by the strict Phase 4.4 gateway protocol validator.

### Phase 4.4 — Engine Protocol & Event Normalization
- Added gateway-side decoding for the existing 4-byte big-endian length-prefixed engine frames.
- Added fragmented-frame and multiple-frame decoding support.
- Added UTF-8 validation and the existing 1 MiB payload limit at the gateway boundary.
- Added typed validation and normalization for supported engine messages.
- Added explicit message types for HELLO, HEARTBEAT, ORDER, TRADE, MARKET_DATA, BOOK_SNAPSHOT, ERROR, and SHUTDOWN.
- Added typed TRADE payload validation covering symbol, price, quantity, taker/maker order identity, taker side, and buy/sell order identity.
- Added normalized typed engine events for supported TRADE events.
- Added explicit rejection of malformed and currently unsupported engine events.
- Added protocol and normalization test coverage.

### Phase 4.3 — Gateway HTTP API
- Completed the versioned gateway application API boundary under /api/v1/....
- Added request/response validation and deterministic HTTP error handling.
- Added upstream status/error mapping and route-level integration coverage.
- Preserved the existing /health and Prometheus metrics behavior.

### Documentation
- Updated the roadmap to reflect completed Phase 4.5 and the start of Phase 4.6.
- Added Phase 4.6.1 contract scope and validation details.

## Current Phase Status

| Phase | Status |
| --- | --- |
| Phase 1 — C++ Order Book & Matching Engine | ✅ Complete |
| Phase 2 — C++ TCP Transport | ✅ Complete |
| Phase 3 — Python Analytics Service | ✅ Complete |
| Phase 3.10 — Analytics Service Hardening | ✅ Complete |
| Phase 4.1 — Gateway Foundation & Architecture | ✅ Complete |
| Phase 4.2 — Gateway Configuration & Runtime Hardening | ✅ Complete |
| Phase 4.3 — Gateway HTTP API | ✅ Complete |
| Phase 4.4 — Engine Protocol & Event Normalization | ✅ Complete |
| Phase 4.5 — WebSocket Gateway | ✅ Complete |
| Phase 4.6 — Python Analytics Integration | ✅ Complete |
| Phase 4.7 — Error Handling, Resilience & Backpressure | ✅ Complete |
| Phase 4.8 — Security Boundaries & Input Hardening | ✅ Complete |
| Phase 4.9 — Operational Logging & Metrics | Complete |
| Phase 4.10 — Testing & Integration Validation | 🚧 In Progress |
| Phase 4.11 — Phase Integration & Exit Criteria | ⏳ Planned |
| Phase 5 — React Dashboard | ⏳ Planned |

## Versioning

This changelog uses milestone-oriented entries while the project remains in active development. Release versions will be introduced when stable release boundaries are defined.
