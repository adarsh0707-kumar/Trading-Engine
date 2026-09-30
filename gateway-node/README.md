# Trading Engine Gateway

The **Trading Engine Gateway** is the external application and client-transport
boundary for the **Cloud-Based Algorithmic Trading Engine**.

It provides the foundation for exposing the trading engine and analytics
services to external clients through HTTP and, in later Phase 4 milestones,
WebSocket connections.

The gateway is implemented using **TypeScript** and **Bun**.

---

## Phase 4.1 — Gateway Foundation & Architecture

Phase 4.1 establishes the initial gateway foundation before adding engine
connectivity, business APIs, WebSocket streaming, or analytics integration.

### Current Capabilities

- Bun runtime
- Bun package manager
- TypeScript
- Strict TypeScript compiler configuration
- Typed gateway configuration
- Fastify HTTP foundation
- Gateway bootstrap
- Graceful shutdown handling
- Health endpoint
- Bun unit tests
- Bun integration tests
- Development and production start commands
- TypeScript build/type-check workflow

### Current HTTP Endpoint

```text
GET /api/health
```

Example response:

```json
{
  "status": "ok",
  "service": "gateway"
}
```

---

## Architecture

The gateway is designed as the application and client-transport boundary of
the trading platform.

```text
                         ┌──────────────────────┐
                         │   External Clients   │
                         │  REST / WebSocket    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Trading Gateway    │
                         │                      │
                         │ TypeScript + Bun     │
                         │ Fastify              │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
             C++ Trading Engine              Python Analytics
             Future Phase 4                  Future Phase 4
```

The gateway does **not** become the source of truth for trading or analytics
logic.

- The **C++ engine** remains authoritative for matching, orders, and trades.
- The **Python analytics service** remains authoritative for analytics, PnL,
  exposure, drawdown, and risk calculations.
- The **gateway** handles external transport, validation, serialization,
  connection lifecycle, and client-facing APIs.

---

## Technology Stack

| Component | Technology |
|---|---|
| Language | TypeScript |
| Runtime | Bun |
| Package Manager | Bun |
| HTTP Framework | Fastify |
| Testing | Bun Test |
| Configuration | Typed environment configuration |
| Future WebSocket | `ws` |
| Future Validation | Zod |
| Future Logging | Pino |
| Future Metrics | Prometheus-compatible metrics |

> Phase 4.1 intentionally keeps the dependency surface small. Components
> marked as future dependencies are introduced in their respective Phase 4
> milestones.

---

## Project Structure

```text
gateway-node/
├── src/
│   ├── api/
│   │   └── health.ts
│   ├── clients/
│   ├── config/
│   │   └── config.ts
│   ├── middleware/
│   ├── observability/
│   ├── services/
│   ├── types/
│   │   └── health.types.ts
│   └── server.ts
│
├── tests/
│   ├── unit/
│   │   └── config.test.ts
│   └── integration/
│       └── health.test.ts
│
├── .env
├── .env.example
├── Dockerfile
├── package.json
├── tsconfig.json
└── bun.lock
```

The local `.env` file is environment-specific and should not be committed to
the repository.

---

## Configuration

Phase 4.1 currently supports the following environment variables:

| Variable | Default | Description |
|---|---|---|
| `GATEWAY_HOST` | `127.0.0.1` | HTTP server bind address |
| `GATEWAY_PORT` | `8080` | HTTP server port |

Example:

```env
GATEWAY_HOST=127.0.0.1
GATEWAY_PORT=8080
```

For local development, copy the example configuration:

```bash
cp .env.example .env
```

Then adjust the values as required.

---

## Development

### Install Dependencies

Use **Bun** for the gateway.

```bash
bun install
```

The Phase 4 gateway does not use npm as its default package manager.

### Run Development Server

```bash
bun run dev
```

The development server runs with Bun's watch mode.

### Run Tests

```bash
bun test
```

Run tests in watch mode:

```bash
bun test --watch
```

### Build / Type Check

```bash
bun run build
```

The build command performs a strict TypeScript type check.

### Start Gateway

```bash
bun run start
```

---

## Health Check

Start the gateway:

```bash
bun run start
```

Then request:

```bash
curl http://127.0.0.1:8080/api/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "gateway"
}
```

---

## Graceful Shutdown

The gateway handles:

- `SIGINT`
- `SIGTERM`

When either signal is received, the gateway attempts to close the Fastify
server cleanly before exiting.

This establishes the lifecycle foundation required for later upstream
connections and WebSocket resources.

---

## Testing Strategy

Phase 4.1 includes two initial test layers.

### Unit Tests

Configuration behavior is tested independently.

```bash
bun test tests/unit/config.test.ts
```

Coverage includes:

- default configuration
- environment overrides
- invalid port rejection

### Integration Tests

The health endpoint is tested through Fastify's request injection.

```bash
bun test tests/integration/health.test.ts
```

Coverage includes:

- health endpoint registration
- HTTP status
- response payload

---

## Phase 4 Roadmap

Phase 4 is divided into the following implementation milestones.

### 4.1 — Gateway Foundation & Architecture

- Bun + TypeScript initialization
- strict TypeScript configuration
- typed configuration boundary
- Fastify foundation
- bootstrap lifecycle
- graceful shutdown
- health endpoint
- initial unit/integration tests

**Status:** In Progress

### 4.2 — Configuration & Environment Management

- complete gateway configuration
- engine connection configuration
- analytics configuration
- timeouts
- reconnect parameters
- request limits
- WebSocket configuration
- logging and metrics configuration
- configuration validation

### 4.3 — C++ Engine TCP Client

- asynchronous TCP client
- existing engine framing protocol
- JSON message handling
- connection lifecycle
- reconnect and backoff
- socket error handling
- connection state

### 4.4 — Engine Protocol & Event Normalization

- typed engine messages
- protocol validation
- event normalization
- domain event representations
- malformed message handling
- consistent event serialization

### 4.5 — REST API

Planned endpoints include:

```text
GET  /api/health
GET  /api/ready
GET  /api/status
GET  /api/market
GET  /api/orderbook
GET  /api/trades
GET  /api/analytics

POST /api/engine/start
POST /api/engine/stop
POST /api/engine/reset
```

### 4.6 — WebSocket Gateway

- WebSocket lifecycle
- subscriptions
- event broadcasting
- client state
- ping/pong
- dead-client cleanup
- per-client queues
- backpressure protection
- slow-consumer handling

### 4.7 — Python Analytics Integration

- analytics service boundary
- analytics connection lifecycle
- latest analytics REST access
- WebSocket analytics updates
- analytics availability state
- event identity preservation

### 4.8 — Error Handling, Resilience & Backpressure

- typed application errors
- REST error responses
- WebSocket errors
- reconnect state machines
- request timeouts
- queue limits
- slow-client protection
- malformed-message isolation
- resource cleanup

### 4.9 — Security Boundaries & Input Hardening

- strict request validation
- request/body size limits
- WebSocket message limits
- CORS
- security headers
- rate-limiting hooks
- safe error responses
- dependency/security checks
- authentication/authorization interfaces

### 4.10 — Operational Logging & Metrics

Structured gateway logging and Prometheus-compatible metrics for:

- HTTP requests
- HTTP errors
- request latency
- WebSocket connections
- WebSocket messages
- engine connection state
- reconnect attempts
- analytics connection state
- upstream messages
- malformed messages
- backpressure events

### 4.11 — Testing & Integration Validation

- unit tests
- integration tests
- gateway ↔ C++ engine tests
- gateway ↔ Python analytics tests
- REST integration tests
- WebSocket integration tests
- reconnect/failure tests
- graceful shutdown tests
- end-to-end event flow validation
- Bun-based CI

### 4.12 — Phase Integration & Exit Criteria

Final Phase 4 validation will confirm:

- Bun-based gateway
- strict TypeScript
- typed configuration
- C++ engine integration
- engine protocol normalization
- REST API
- WebSocket gateway
- Python analytics integration
- resilience and backpressure
- security boundaries
- operational logging
- metrics
- unit/integration testing
- CI validation
- documentation updates
- no regression in Phases 1–3

---

## Design Principles

### Gateway Is Not the Trading Engine

The gateway must not duplicate matching-engine responsibilities.

Trading state remains authoritative in the C++ engine.

### Gateway Is Not the Analytics Engine

The gateway must not independently calculate:

- VWAP
- SMA
- EMA
- PnL
- exposure
- drawdown
- risk limits
- risk events

Those responsibilities remain within the Python analytics service.

### Thin Transport Layer

HTTP and WebSocket handlers should remain thin.

Business logic should live behind typed services and clients rather than
inside route handlers.

### Explicit Boundaries

Communication between components should use explicit contracts:

```text
Client
   │
   ▼
Gateway API / WebSocket
   │
   ├── C++ Engine Client
   │
   └── Python Analytics Client
```

### Fail Safely

A malformed request, upstream message, or client connection should not crash
the entire gateway process.

---

## Docker

A Dockerfile is included as the foundation for the future containerized
gateway deployment.

Build and deployment integration will be expanded as the gateway reaches the
later Phase 4 milestones and the platform-level Docker architecture is
implemented.

---

## Related Documentation

Project-level architecture and implementation decisions are documented in:

```text
docs/02-architecture.md
docs/05-roadmap-and-phases.md
docs/06-development-guide.md
docs/09-testing-strategy.md
docs/17-changelog.md
```

The Bun gateway architecture decision is documented as **ADR-007**.

---

## Current Status

```text
Phase 1  — Core Matching Engine           Complete
Phase 2  — Engine Protocol               Complete
Phase 3  — Analytics & Risk               Complete
Phase 4  — Gateway                        In Progress

Phase 4.1  — Gateway Foundation           In Progress
Phase 4.2  — Configuration                Planned
Phase 4.3  — C++ TCP Client               Planned
Phase 4.4  — Protocol Normalization       Planned
Phase 4.5  — REST API                     Planned
Phase 4.6  — WebSocket Gateway            Planned
Phase 4.7  — Python Analytics Integration Planned
Phase 4.8  — Resilience & Backpressure    Planned
Phase 4.9  — Security Hardening           Planned
Phase 4.10 — Logging & Metrics            Planned
Phase 4.11 — Testing & Validation         Planned
Phase 4.12 — Phase Integration            Planned
```

---

## License

See the repository-level license for project licensing information.
