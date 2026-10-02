# Changelog

All notable changes to the Cloud-Based Algorithmic Trading Engine are documented here.

This project is an educational trading-infrastructure simulation. It does not connect to a real exchange or execute real financial transactions.

## [Unreleased]

### Next — Phase 4.5 WebSocket Gateway
- Provide the configured browser-facing WebSocket endpoint.
- Add connection lifecycle and subscription handling.
- Stream normalized gateway events to clients.
- Add heartbeat/ping-pong and dead-client cleanup.
- Add per-client queue/backpressure limits and slow-consumer protection.
- Preserve graceful gateway shutdown behavior.

## [2026-10-02]

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
- Completed the versioned gateway application API boundary under `/api/v1/...`.
- Added request/response validation and deterministic HTTP error handling.
- Added upstream status/error mapping and route-level integration coverage.
- Preserved the existing `/health` and Prometheus metrics behavior.

### Documentation
- Updated the roadmap to reflect completed Phase 4.3 and Phase 4.4 milestones.
- Updated the current milestone to Phase 4.5 WebSocket Gateway.
- Added Phase 4.4 implementation details and validation scope to the historical changelog.

## [2026-09-30]

### Phase 4.2 — Gateway Configuration & Runtime Hardening
- Completed typed gateway configuration and environment management.
- Added validation for gateway host, ports, timeouts, limits, CORS, reconnect parameters, logging, and metrics settings.
- Added immutable configuration objects and deterministic validation errors.
- Added complete `.env.example` coverage for gateway configuration.
- Integrated runtime CORS with `@fastify/cors`.
- Integrated Prometheus-compatible metrics with `prom-client`.
- Added configurable metrics path and disabled-mode behavior.
- Added integration coverage for CORS and metrics.
- Preserved idempotent gateway start/stop lifecycle behavior.
- Validation: gateway build passes; gateway test suite passes with 21 tests.

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
| Phase 4.5 — WebSocket Gateway | ⏳ Next |
| Phase 4.6 — Python Analytics Integration | ⏳ Planned |
| Phase 4.7 — Error Handling, Resilience & Backpressure | ⏳ Planned |
| Phase 4.8 — Security Boundaries & Input Hardening | ⏳ Planned |
| Phase 4.9 — Operational Logging & Metrics | ⏳ Planned |
| Phase 4.10 — Testing & Integration Validation | ⏳ Planned |
| Phase 4.11 — Phase Integration & Exit Criteria | ⏳ Planned |
| Phase 5 — React Dashboard | ⏳ Planned |

## Versioning

This changelog uses milestone-oriented entries while the project remains in active development. Release versions will be introduced when stable release boundaries are defined.
