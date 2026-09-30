# Changelog

All notable changes to the Cloud-Based Algorithmic Trading Engine are documented here.

This project is an educational trading-infrastructure simulation. It does not connect to a real exchange or execute real financial transactions.

## [Unreleased]

### Next — Phase 4.3 Gateway HTTP API
- Introduce the versioned application API boundary under `/api/v1/...`.
- Add request/response contracts, validation, deterministic HTTP errors, and integration tests.
- Preserve the existing `/health`, CORS, and Prometheus metrics behavior.

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

### Documentation
- Corrected roadmap status for completed Phase 3.10, Phase 4.1, and Phase 4.2 milestones.
- Documented the currently implemented gateway operational endpoints.
- Distinguished implemented endpoints from planned application API routes.
- Added this changelog as the historical implementation record.

## Current Phase Status

| Phase | Status |
| --- | --- |
| Phase 1 — C++ Order Book & Matching Engine | ✅ Complete |
| Phase 2 — C++ TCP Transport | ✅ Complete |
| Phase 3 — Python Analytics Service | ✅ Complete |
| Phase 3.10 — Analytics Service Hardening | ✅ Complete |
| Phase 4.1 — Gateway Foundation & Architecture | ✅ Complete |
| Phase 4.2 — Gateway Configuration & Runtime Hardening | ✅ Complete |
| Phase 4.3 — Gateway HTTP API | ⏳ Next |
| Phase 4.4 — Engine Protocol & Event Normalization | ⏳ Planned |
| Phase 4.5 — WebSocket Gateway | ⏳ Planned |
| Phase 4.6 — Python Analytics Integration | ⏳ Planned |
| Phase 4.7 — Error Handling, Resilience & Backpressure | ⏳ Planned |
| Phase 4.8 — Security Boundaries & Input Hardening | ⏳ Planned |
| Phase 4.9 — Operational Logging & Metrics | ⏳ Planned |
| Phase 4.10 — Testing & Integration Validation | ⏳ Planned |
| Phase 4.11 — Phase Integration & Exit Criteria | ⏳ Planned |
| Phase 5 — React Dashboard | ⏳ Planned |

## Versioning

This changelog uses milestone-oriented entries while the project remains in active development. Release versions will be introduced when stable release boundaries are defined.
