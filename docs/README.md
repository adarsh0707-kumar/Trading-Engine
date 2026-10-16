# Cloud-Based Algorithmic Trading Engine — Documentation

This directory contains the engineering documentation for the **Cloud-Based Algorithmic Trading Engine**, a simulated polyglot trading platform.

> **Important:** This is an educational/systems-engineering simulation. It is not connected to a real exchange and does not execute real financial transactions.

## Documentation Map

| File | Purpose |
|---|---|
| `01-product-requirements.md` | Product scope, requirements, goals, acceptance criteria |
| `02-architecture.md` | Service architecture, data flow, decisions, failure handling |
| `03-data-model.md` | Orders, trades, analytics events, schemas, calculations |
| `04-api-reference.md` | REST and WebSocket API contracts |
| `05-roadmap-and-phases.md` | Implementation phases, milestones, definition of done |
| `06-development-guide.md` | Repository structure, development workflow, coding standards |
| `07-security.md` | Threat model, authentication, authorization, validation, hardening |
| `08-gap-analysis.md` | MVP vs production-style architecture and future gaps |
| `09-testing-strategy.md` | Unit, integration, contract, E2E, performance and failure testing |
| `10-glossary.md` | Definitions of domain and engineering terminology |
| `11-risk-limits-and-enforcement.md` | Risk-limit defaults, event flow, runtime checks, and the distinction between risk reporting and trade enforcement |

## Architecture at a Glance

```text
┌──────────────────────┐
│  C++ Trading Engine  │
│  Order Book + Match  │
└──────────┬───────────┘
           │ socket events
           ▼
┌──────────────────────┐
│ Python Analytics     │
│ VWAP / MA / PnL/Risk │
└──────────┬───────────┘
           │ enriched events
           ▼
┌──────────────────────┐
│ Node.js Gateway      │
│ REST + WebSocket     │
└──────────┬───────────┘
           │ live stream
           ▼
┌──────────────────────┐
│ React + TypeScript   │
│ Trading Dashboard    │
└──────────────────────┘
```

## Core Engineering Themes

The project is intended to demonstrate:

- C++ data structures and algorithms.
- Order matching and price-time priority.
- Inter-process communication.
- Event-driven architecture.
- Python numerical analytics.
- REST API design.
- WebSocket streaming.
- React/TypeScript UI engineering.
- Docker-based service orchestration.
- Testing and deterministic replay.
- Backpressure and failure handling.
- Security boundaries.
- Performance measurement.

## Recommended Build Order

```text
1. Specification
2. C++ order book
3. C++ matching engine
4. C++ socket transport
5. Python analytics
6. Node gateway
7. React dashboard
8. Docker Compose
9. Testing and hardening
10. Benchmarking
11. Optional performance transports
```

## Current Implementation Status

- Phase 3 — Python Analytics: ✅ Complete
- Phase 4.1 — Gateway Foundation: ✅ Complete
- Phase 4.2 — Gateway Configuration & Runtime Hardening: ✅ Complete
- Phase 4.3 — Gateway HTTP API: ✅ Complete
- Phase 4.4 — Engine Protocol & Event Normalization: ✅ Complete
- Phase 4.5 — WebSocket Gateway: ✅ Complete
- Phase 4.6 — Python Analytics Integration: ✅ Complete
- Phase 4.7 — Error Handling, Resilience & Backpressure: ✅ Complete
- Phase 4 — Gateway: ✅ Complete
- Phase 5.10 — Loading, Error, and Stale-Data UX: ✅ Complete
- Phase 5.11 — Dashboard production polish: ✅ Complete for current milestone scope
- Phase 5.12 — Halted-State Market Data: ✅ Complete — PR #132
- Phase 5.13 — Data Integrity & Observability: ✅ Complete — PRs #133 and #134
- Phase 5.14 — Full Runtime Integration Validation: 🚧 In progress; runtime smoke checks and isolated integration tests pass, while live trade/risk-event delivery and browser-level WebSocket recovery remain outstanding

## Documentation Rule

Documentation must evolve with implementation.

If an API, event schema, architecture decision, or requirement changes, update the corresponding document in the same change.

## Accuracy Rule

Do not describe measured performance using unverified numbers.

For example, prefer:

> "The engine sustained X events/sec on the documented test machine."

over:

> "The engine processes millions of events per second."

unless the latter has actually been measured and documented.

## Portfolio Positioning

The project should be presented as a **trading-infrastructure simulation and distributed-systems project**, not as a real exchange or financial product.

The strongest engineering story is the two distinct live-data paths:

```text
MARKET_DATA → Gateway market snapshot → WebSocket → dashboard
TRADE       → Gateway trade history ─┬→ WebSocket → dashboard
                                     └→ analytics → PostgreSQL
```

Market-price updates are independent of trade execution and can continue while the engine is risk-halted. A risk halt still prevents matching and trade execution.

and the engineering trade-offs involved at each boundary.

---

If this project was useful to you, consider [![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-yellow?logo=buy-me-a-coffee\&logoColor=white)](https://buymeacoffee.com/adarsh12kumar)

