# Cloud-Based Algorithmic Trading Engine

A polyglot trading **simulation platform** built from the socket layer up: a C++ matching engine, Python analytics service, Bun/Fastify gateway, PostgreSQL persistence, and a React dashboard.

The project focuses on the engineering problems behind real-time trading infrastructure — order-book correctness, price-time matching, framed TCP protocols, service boundaries, backpressure, resilience, observability, and live browser updates.

> **Status:** Active development  
> **Current focus:** Phase 5 dashboard production hardening and final validation  
> **Important:** This is a simulation. It does not connect to an exchange or execute real financial trades.

## Architecture

```text
                    Simulated Market
                           │
                           ▼
              ┌────────────────────────┐
              │    C++ Trading Engine   │
              │                        │
              │ Order Book             │
              │ Price-Time Matching    │
              │ Trade Generation       │
              │ TCP Transport          │
              └───────────┬────────────┘
                          │
                   framed TCP events
                          │
                          ▼
              ┌────────────────────────┐
              │    Python Analytics    │
              │                        │
              │ Indicators             │
              │ Portfolio / P&L        │
              │ Risk / Drawdown        │
              │ PostgreSQL Persistence │
              └───────────┬────────────┘
                          │
                    analytics state
                          │
                          ▼
              ┌────────────────────────┐
              │    Bun + Fastify       │
              │       Gateway          │
              │                        │
              │ REST API               │
              │ WebSocket              │
              │ Validation             │
              │ Rate Limiting          │
              │ Health / Metrics       │
              └───────────┬────────────┘
                          │
                    HTTP / WebSocket
                          │
                          ▼
              ┌────────────────────────┐
              │     React Dashboard    │
              │                        │
              │ Market State           │
              │ Order Book             │
              │ Recent Trades          │
              │ Analytics / Risk       │
              │ System Status          │
              └────────────────────────┘
```

### End-to-end event path

```text
Market simulation
      ↓
C++ order book
      ↓
Price-time matching
      ↓
TRADE event
      ↓
Gateway engine-event client
      ↓
Python analytics
      ↓
PostgreSQL
      ↓
Gateway state / WebSocket
      ↓
React dashboard
```

The browser talks only to the Gateway. It does not connect directly to the C++ engine or Python service.

## What is implemented

### C++ trading engine

- Limit-order matching with price-time priority
- Order validation and order-book management
- Partial fills
- Order cancellation
- Deterministic trade generation
- TCP transport
- 4-byte big-endian length-prefixed framing
- UTF-8 JSON payload validation
- HELLO / HEARTBEAT handling
- Connection lifecycle and recovery behavior
- Unit, integration, and sanitizer coverage

### Python analytics

- Streaming trade processing
- VWAP, SMA, EMA, and volatility calculations
- Position tracking
- Realized and unrealized P&L
- Exposure and drawdown
- Risk limits and risk events
- PostgreSQL persistence
- Prometheus-compatible metrics
- Backpressure and bounded recovery behavior
- Gateway-to-analytics contract validation

### Gateway

The Gateway is implemented with **Bun + TypeScript + Fastify**.

- Versioned REST API under `/api/v1`
- WebSocket endpoint at `/ws`
- Typed engine-event normalization
- Request validation and deterministic API errors
- CORS configuration
- Rate limiting
- Request-size limits
- Health and readiness boundaries
- Prometheus metrics
- Bounded WebSocket outbound queues
- Slow-consumer protection
- Engine and analytics dependency handling

### React dashboard

The dashboard uses **React 19 + TypeScript + Vite + React Router**.

Implemented dashboard areas include:

- Live market state
- Recent trades
- Live order-book snapshot
- Analytics and indicators
- Portfolio / P&L / risk views
- Engine, gateway, and analytics status
- REST client with typed API errors
- WebSocket subscriptions and reconnect handling
- Loading, error, empty, and stale-data states

## Technology stack

| Layer | Technology |
| --- | --- |
| Matching engine | C++17 |
| Build | CMake / Make |
| Engine transport | TCP sockets |
| Wire format | UTF-8 JSON with 4-byte big-endian framing |
| Analytics | Python |
| Database | PostgreSQL 17 |
| Gateway runtime | Bun |
| Gateway | TypeScript + Fastify |
| Browser API | REST + WebSocket |
| Frontend | React 19 + TypeScript |
| Frontend build | Vite |
| Containers | Docker |
| Local orchestration | Docker Compose |
| Testing | C++ tests, Pytest, Bun test |
| CI | GitHub Actions |
| Metrics | Prometheus-compatible endpoints |

## Repository structure

```text
Trading-Engine/
├── engine-cpp/          # C++ engine, order book, matching, transport
├── analytics-py/        # Python analytics, risk, persistence, metrics
├── gateway-node/        # Bun/Fastify REST + WebSocket gateway
├── dashboard-react/     # React dashboard
├── shared/              # Shared schemas and contracts
├── docs/                # Architecture, API, security, testing, ADRs
├── scripts/              # Build/test/development helpers
├── tests/e2e/            # End-to-end coverage
├── docker-compose.yml
├── Makefile
└── README.md
```

## Trading model

The matching engine follows standard price-time priority for the simulation.

**Buy orders:** higher price has priority; at the same price, earlier orders have priority.

**Sell orders:** lower price has priority; at the same price, earlier orders have priority.

Example:

```text
BUY
100.50  → first
100.50  → second
100.40  → third
```

If a 100-share buy order matches a 40-share sell order:

```text
Trade:     40 shares
Remaining: 60 shares on the buy order
```

This gives the engine deterministic partial-fill behavior rather than treating matching as a simple one-shot transaction.

## Internal protocol

The engine-to-service transport uses:

```text
┌──────────────┬─────────────────────────────┐
│ 4-byte BE    │ UTF-8 JSON payload          │
│ length       │ max 1 MiB                   │
└──────────────┴─────────────────────────────┘
```

The protocol supports explicit message types including:

```text
HELLO
HEARTBEAT
ORDER
TRADE
MARKET_DATA
BOOK_SNAPSHOT
ERROR
SHUTDOWN
```

The Gateway validates and normalizes supported engine messages before exposing them to browser clients or forwarding trade data to analytics.

## REST API

Base URL:

```text
http://localhost:8080
```

### Implemented application endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Gateway process health |
| GET | `/api/v1/status` | Gateway / engine / analytics status |
| GET | `/api/v1/market` | Current market state |
| GET | `/api/v1/orderbook` | Current engine order-book snapshot |
| GET | `/api/v1/trades` | Recent trades |
| GET | `/api/v1/analytics` | Latest analytics state |
| POST | `/api/v1/engine/start` | Engine-control contract |
| POST | `/api/v1/engine/stop` | Engine-control contract |
| POST | `/api/v1/engine/reset` | Engine-control contract |
| GET | `/metrics` | Prometheus metrics when enabled |

Dependency failures are represented explicitly rather than replaced with fabricated data. Application errors use a structured response containing an error code, message, and request ID.

Full contracts live in [`docs/04-api-reference.md`](docs/04-api-reference.md).

## WebSocket API

Endpoint:

```text
ws://localhost:8080/ws
```

Clients subscribe to supported event types:

```json
{
  "action": "subscribe",
  "events": ["TRADE", "ANALYTICS_UPDATE", "RISK_EVENT"]
}
```

The Gateway provides:

- Explicit subscribe / unsubscribe handling
- Normalized event envelopes
- Heartbeat and dead-client cleanup
- Bounded per-client queues
- Slow-consumer protection
- Clean shutdown behavior

The React client reconnects with bounded backoff and restores subscriptions after reconnect.

## Docker runtime

The complete local runtime is orchestrated with Docker Compose.

### Services

| Service | Container port | Host default |
| --- | ---: | ---: |
| C++ engine | 9000 | 9000 |
| Analytics receiver | 8000 | internal |
| Analytics metrics | 9101 | 9101 |
| Gateway | 8080 | 8080 |
| Dashboard | 80 | 5173 |
| PostgreSQL | 5432 | 5432 |

### Start everything

```bash
docker compose up -d --build
```

Check service state:

```bash
docker compose ps
```

Follow logs:

```bash
docker compose logs -f
```

Check Gateway health:

```bash
curl http://localhost:8080/api/health
```

Check dependency readiness:

```bash
curl http://localhost:8080/api/v1/status
```

Open the dashboard:

```text
http://localhost:5173
```

Stop the runtime:

```bash
docker compose down
```

Remove the database volume too:

```bash
docker compose down -v
```

## Local development

### Prerequisites

- Git
- GCC / G++
- CMake
- Make
- Python 3
- Bun 1.3+
- Docker
- Docker Compose

### Gateway

```bash
cd gateway-node
bun install
bun run dev
```

Build and test:

```bash
bun run build
bun test
```

### Dashboard

```bash
cd dashboard-react
bun install
bun run dev
```

Build and test:

```bash
bun run build
bun test
```

### C++ engine

```bash
cd engine-cpp
mkdir -p build
cd build
cmake ..
make -j$(nproc)
```

### Python analytics

```bash
cd analytics-py
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

For the most reproducible setup, use the Docker Compose runtime.

## Testing

Testing is layered across the system:

```text
Unit
  ↓
Component integration
  ↓
Cross-service contract tests
  ↓
Runtime integration
  ↓
End-to-end validation
```

Examples:

```bash
# Gateway
cd gateway-node
bun test

# Dashboard
cd dashboard-react
bun test

# Python
cd analytics-py
pytest

# Full runtime smoke test
cd gateway-node
bun test tests/runtime-stack.integration.test.ts
```

The runtime integration test validates the real service path rather than a mocked dashboard-only flow.

## Observability and reliability

The project treats failure handling as part of the architecture.

Current areas include:

- Health and readiness checks
- Structured service logging
- Prometheus metrics
- Request IDs
- Dependency failure mapping
- Bounded queues
- Backpressure handling
- Engine reconnect behavior
- WebSocket slow-consumer protection
- Graceful shutdown
- Input and payload-size validation
- Security-focused gateway tests

The design principle is simple:

> **A slow or failed consumer should not silently become a system-wide failure.**

## Security boundary

This is a simulation, but the service boundaries are intentionally hardened.

Implemented protections include:

- Input validation
- Request-size limits
- Rate limiting
- CORS allowlisting
- WebSocket validation
- Deterministic error handling
- Dependency isolation
- Containerized local runtime
- Security-focused automated tests
- Secret/configuration separation

The default Docker Compose configuration intentionally keeps authentication disabled for local development. Authentication and authorization remain a later platform concern.

Never commit real credentials or secrets to `.env` files.

## Performance

Performance is measured only when there is a reproducible benchmark behind the number. The README therefore does **not** claim arbitrary orders/sec or latency figures.

The performance work is centered on:

- Matching latency
- Trade throughput
- Socket throughput
- Analytics processing latency
- Gateway latency
- WebSocket delivery
- CPU and memory usage
- P95/P99 behavior

Optimization follows:

```text
Correctness
    ↓
Profile
    ↓
Find bottleneck
    ↓
Optimize
    ↓
Benchmark
    ↓
Regression test
```

Potential future optimizations include binary protocols, shared memory, zero-copy paths, memory pools, cache-aware structures, batching, and lock-free structures — but only where measurement justifies the added complexity.

## Current implementation status

| Area | Status |
| --- | --- |
| C++ order book + matching | ✅ Complete |
| C++ TCP transport | ✅ Complete |
| Python streaming analytics | ✅ Complete |
| Risk analytics | ✅ Complete |
| PostgreSQL persistence | ✅ Complete |
| Gateway REST API | ✅ Complete |
| Gateway WebSocket | ✅ Complete |
| Gateway resilience / backpressure | ✅ Complete |
| Gateway security boundaries | ✅ Complete |
| Docker full-stack runtime | ✅ Complete |
| React dashboard foundation | ✅ Complete |
| Live market + trades | ✅ Complete |
| Order-book dashboard | ✅ Complete |
| Analytics / portfolio / risk views | ✅ Complete |
| Loading / error / stale-data UX | ✅ Complete |
| Dashboard production polish | 🚧 In progress |
| Final browser/E2E validation | ⏳ Planned |
| Historical analytics | ⏳ Planned |
| Cloud deployment | ⏳ Planned |

Detailed milestone history is maintained in [`docs/05-roadmap-and-phases.md`](docs/05-roadmap-and-phases.md).

## Architecture decisions

The important design decisions are documented as ADRs:

- [ADR-001 — Polyglot architecture](docs/decisions/ADR-001-polyglot-architecture.md)
- [ADR-002 — Socket IPC](docs/decisions/ADR-002-socket-ipc.md)
- [ADR-003 — JSON wire format](docs/decisions/ADR-003-json-wire-format.md)
- [ADR-004 — WebSocket gateway](docs/decisions/ADR-004-websocket-gateway.md)
- [ADR-005 — Docker Compose](docs/decisions/ADR-005-docker-compose.md)
- [ADR-006 — Shared memory as a future optimization](docs/decisions/ADR-006-shared-memory-future.md)

The repository also contains documentation for architecture, API contracts, security, testing, development, data models, and known gaps under `docs/`.

## Roadmap

### Next

- Complete dashboard production hardening
- Finish browser-level validation
- Improve measured frontend performance
- Expand runtime and failure-path validation

### Later

- Historical analytics
- More realistic strategy simulation
- Multiple symbols/accounts
- Advanced order types
- Replayable market sessions
- Additional risk metrics
- Cloud deployment
- Distributed event infrastructure where justified by scale

## Limitations

This project deliberately does **not** model a real exchange.

- Market data is simulated.
- No real exchange connectivity exists.
- No real-money execution exists.
- Market microstructure is simplified.
- Risk and transaction-cost models are simplified.
- Authentication is disabled in the default local Compose configuration.
- Cloud deployment is not part of the current validated runtime.
- Performance numbers are not claimed without reproducible benchmarks.

Do not use this project for real-money trading.

## Why this project

This project is primarily a systems-engineering exercise.

It brings together:

```text
C++ systems programming
        +
Networking / TCP protocols
        +
Order-book algorithms
        +
Python quantitative analytics
        +
PostgreSQL persistence
        +
TypeScript service boundaries
        +
WebSocket real-time delivery
        +
React visualization
        +
Docker / CI
        +
Testing / observability / resilience
```

The goal is not to build the biggest stack possible. It is to understand the boundaries between components, make those boundaries explicit, test failure modes, and optimize only after correctness is established.

## Contributing

For changes:

1. Create a focused branch.
2. Add or update tests.
3. Run the relevant service tests.
4. Run the full validation path when applicable.
5. Update documentation when behavior or contracts change.
6. Open a focused pull request.

Use conventional commit prefixes such as `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `perf:`, and `ci:`.

## License

No formal open-source license has been declared yet. Until a license is added to the repository, the project should be treated as an educational/portfolio project rather than as software released under a standard open-source license.

## Author

**Adarsh Kumar**

Systems-oriented software engineer building from the socket layer up.

---

> **Engineering principle:** Correctness first. Measure second. Optimize third.
