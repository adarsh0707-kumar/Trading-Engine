# Cloud-Based Algorithmic Trading Engine

A production-style, polyglot trading simulation platform designed to demonstrate how modern algorithmic trading infrastructure can be structured across high-performance systems, analytics, APIs, real-time communication, and visualization.

> **Project status:** Active development
> **Primary goal:** Build a realistic, modular trading-engine simulation for learning, experimentation, benchmarking, and portfolio demonstration.

---

## Table of Contents

- [Overview](#overview)
- [Goals](#goals)
- [Architecture](#architecture)
- [Data Flow](#data-flow)
- [Services](#services)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Core Trading Concepts](#core-trading-concepts)
- [Order Book](#order-book)
- [Matching Engine](#matching-engine)
- [Analytics Engine](#analytics-engine)
- [Communication](#communication)
- [API Reference](#api-reference)
- [WebSocket Events](#websocket-events)
- [Configuration](#configuration)
- [Getting Started](#getting-started)
- [Docker](#docker)
- [Testing](#testing)
- [Performance](#performance)
- [Observability](#observability)
- [Security](#security)
- [Architecture Decisions](#architecture-decisions)
- [Roadmap](#roadmap)
- [Future Improvements](#future-improvements)
- [Limitations](#limitations)
- [Project Value](#project-value)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## Overview

The **Cloud-Based Algorithmic Trading Engine** is a distributed trading simulation platform that models the major components found in modern electronic trading systems.

The system generates simulated market data, maintains an order book, matches buy and sell orders using price-time priority, produces trade events, calculates financial analytics, exposes REST APIs and WebSockets, and presents the results through a real-time React dashboard.

The platform follows a polyglot architecture:

```text
┌───────────────────────┐
│   Simulated Market    │
│        Data           │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│     C++ Trading       │
│        Engine         │
│                       │
│ • Market Simulation   │
│ • Order Book          │
│ • Matching Engine     │
│ • Trade Generation    │
└───────────┬───────────┘
            │ TCP / Unix Socket
            ▼
┌───────────────────────┐
│   Python Analytics    │
│                       │
│ • VWAP                │
│ • SMA / EMA           │
│ • PnL                 │
│ • Exposure            │
│ • Drawdown            │
└───────────┬───────────┘
            │ IPC / API
            ▼
┌───────────────────────┐
│    Node.js Gateway    │
│                       │
│ • REST API            │
│ • WebSocket           │
│ • Routing             │
│ • Rate Limiting       │
│ • Middleware          │
└───────────┬───────────┘
            │ HTTP / WebSocket
            ▼
┌───────────────────────┐
│    React Dashboard    │
│                       │
│ • Charts              │
│ • Order Book          │
│ • Trades              │
│ • Metrics              │
│ • Engine Controls     │
└───────────────────────┘
```

---

## Goals

### Primary Goals

- Build a realistic trading-engine simulation.
- Demonstrate high-performance C++ systems programming.
- Demonstrate Python-based quantitative analytics.
- Demonstrate TypeScript/Node.js API development.
- Demonstrate React real-time visualization.
- Implement deterministic order matching.
- Support real-time market and trade events.
- Provide a modular service-oriented architecture.
- Containerize the complete platform.
- Provide automated testing and CI/CD.
- Create a portfolio-quality engineering project.

### Non-Goals

This project is not intended to:

- Execute real financial trades.
- Connect to a real stock exchange.
- Handle real customer money.
- Provide financial advice.
- Replace a production exchange matching engine.

---

# Architecture

The platform uses separate services so each component can be developed, tested, benchmarked, and optimized independently.

```text
                         ┌──────────────────────┐
                         │    Market Simulator   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌────────────────────────────┐
                    │       C++ Engine            │
                    │                            │
                    │  Market Data               │
                    │  Order Book                │
                    │  Matching Engine           │
                    │  Trade Events              │
                    └────────────┬───────────────┘
                                 │
                                 │ IPC
                                 ▼
                    ┌────────────────────────────┐
                    │     Python Analytics        │
                    │                            │
                    │ Indicators / Risk / PnL    │
                    └────────────┬───────────────┘
                                 │
                                 │
                                 ▼
                    ┌────────────────────────────┐
                    │      Node.js Gateway        │
                    │                            │
                    │ REST + WebSocket + Auth    │
                    └────────────┬───────────────┘
                                 │
                                 │ HTTP / WS
                                 ▼
                    ┌────────────────────────────┐
                    │       React Dashboard       │
                    └────────────────────────────┘
```

---

# Data Flow

A typical event flows through the system as follows:

```text
Market Tick
    │
    ▼
Market Simulator
    │
    ▼
C++ Engine
    │
    ├── Update Order Book
    │
    ├── Match Orders
    │
    └── Generate Trade Event
             │
             ▼
       Python Analytics
             │
             ├── VWAP
             ├── SMA / EMA
             ├── PnL
             ├── Exposure
             └── Drawdown
             │
             ▼
       Node.js Gateway
             │
             ├── REST API
             └── WebSocket
                    │
                    ▼
             React Dashboard
```

---

# Services

## 1. C++ Trading Engine

The C++ service is the performance-critical core of the platform.

Responsibilities:

- Market-data simulation.
- Order creation.
- Order validation.
- Order-book management.
- Price-time-priority matching.
- Partial fills.
- Trade generation.
- Engine lifecycle management.
- Low-level network communication.

### Why C++?

C++ provides:

- Low-level memory control.
- Predictable performance.
- Efficient data structures.
- Multithreading capabilities.
- Strong suitability for latency-sensitive systems.

---

## 2. Python Analytics Engine

The analytics service consumes market and trade events generated by the C++ engine.

Responsibilities:

- Market indicators.
- Portfolio analytics.
- PnL calculation.
- Exposure calculation.
- Drawdown calculation.
- Risk metrics.
- Aggregated analytics events.

Python is used because of its strong ecosystem for quantitative and numerical workloads.

---

## 3. Node.js Gateway

The gateway provides the external interface for the platform.

Responsibilities:

- REST API.
- WebSocket streaming.
- Service routing.
- Request validation.
- Rate limiting.
- Middleware.
- Error handling.
- Configuration management.

TypeScript is used for strong typing and maintainability.

---

## 4. React Dashboard

The dashboard provides real-time visualization.

Responsibilities:

- Market-price charts.
- Order-book visualization.
- Recent trades.
- Analytics.
- Portfolio metrics.
- Engine status.
- Simulation controls.

---

# Technology Stack

| Layer                | Technology                                           |
| -------------------- | ---------------------------------------------------- |
| Trading Engine       | C++                                                  |
| Build System         | CMake / Make                                         |
| Analytics            | Python                                               |
| Numerical Processing | NumPy / Pandas                                       |
| API Gateway          | Node.js                                              |
| Gateway Language     | TypeScript                                           |
| Frontend             | React + TypeScript                                   |
| Frontend Build       | Vite                                                 |
| Charts               | Recharts                                             |
| Real-Time Transport  | WebSocket                                            |
| IPC                  | TCP / Unix Domain Socket                             |
| Wire Format          | JSON                                                 |
| Containerization     | Docker                                               |
| Orchestration        | Docker Compose                                       |
| Testing              | C++ tests / Pytest / Node test tooling / React tests |
| CI/CD                | GitHub Actions                                       |

---

# Repository Structure

```text
Trading-Engine/
│
├── .github/
│   ├── workflows/
│   │   ├── build.yml
│   │   ├── test.yml
│   │   ├── lint.yml
│   │   ├── docker.yml
│   │   └── security.yml
│   │
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   │
│   └── pull_request_template.md
│
├── engine-cpp/
│   ├── include/
│   │   ├── engine/
│   │   ├── orderbook/
│   │   ├── matching/
│   │   ├── network/
│   │   ├── market/
│   │   └── common/
│   │
│   ├── src/
│   │   ├── engine/
│   │   ├── orderbook/
│   │   ├── matching/
│   │   ├── network/
│   │   ├── market/
│   │   └── main.cpp
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── fixtures/
│   │
│   ├── config/
│   ├── Makefile
│   ├── CMakeLists.txt
│   └── Dockerfile
│
├── analytics-py/
│   ├── src/
│   │   ├── analytics/
│   │   ├── indicators/
│   │   ├── risk/
│   │   ├── portfolio/
│   │   ├── transport/
│   │   └── main.py
│   │
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   │
│   ├── config/
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
│
├── gateway-node/
│   ├── src/
│   │   ├── api/
│   │   ├── websocket/
│   │   ├── services/
│   │   ├── middleware/
│   │   ├── config/
│   │   └── server.ts
│   │
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   │
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
│
├── dashboard-react/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   ├── types/
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── public/
│   ├── tests/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── shared/
│   ├── schemas/
│   │   ├── order.schema.json
│   │   ├── trade.schema.json
│   │   ├── tick.schema.json
│   │   └── analytics.schema.json
│   │
│   └── types/
│
├── docs/
│   ├── 01-product-requirements.md
│   ├── 02-architecture.md
│   ├── 03-data-model.md
│   ├── 04-api-reference.md
│   ├── 05-roadmap-and-phases.md
│   ├── 06-development-guide.md
│   ├── 07-security.md
│   ├── 08-gap-analysis.md
│   ├── 09-testing-strategy.md
│   ├── 10-glossary.md
│   │
│   ├── diagrams/
│   │   ├── system-architecture.png
│   │   ├── data-flow.png
│   │   ├── service-interaction.png
│   │   ├── order-book-flow.png
│   │   └── deployment-architecture.png
│   │
│   └── decisions/
│       ├── ADR-001-polyglot-architecture.md
│       ├── ADR-002-socket-ipc.md
│       ├── ADR-003-json-wire-format.md
│       ├── ADR-004-websocket-gateway.md
│       ├── ADR-005-docker-compose.md
│       └── ADR-006-shared-memory-future.md
│
├── scripts/
│   ├── build.sh
│   ├── test.sh
│   ├── dev.sh
│   └── clean.sh
│
├── tests/
│   └── e2e/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Makefile
└── README.md
```

---

# Core Trading Concepts

The engine models common exchange-style concepts.

## Order

An order represents an instruction to buy or sell an asset.

Example:

```json
{
  "order_id": "ORD-10001",
  "symbol": "AAPL",
  "side": "BUY",
  "price": 185.50,
  "quantity": 100,
  "type": "LIMIT"
}
```

## Trade

A trade is generated when compatible buy and sell orders are matched.

```json
{
  "trade_id": "TRD-50001",
  "symbol": "AAPL",
  "price": 185.50,
  "quantity": 50,
  "buy_order_id": "ORD-10001",
  "sell_order_id": "ORD-10002"
}
```

---

# Order Book

The order book contains outstanding buy and sell orders.

```text
ASKS
Price        Quantity
---------------------
186.20          100
186.00          250
185.80          150
---------------------
185.60          200
185.50          300
185.40          150
---------------------
BIDS
```

The best bid is the highest buy price.

The best ask is the lowest sell price.

The spread is:

```text
Spread = Best Ask - Best Bid
```

---

# Matching Engine

Orders are matched using **price-time priority**.

### Buy Priority

Higher price first.

If two buy orders have the same price:

Earlier order first.

### Sell Priority

Lower price first.

If two sell orders have the same price:

Earlier order first.

Example:

```text
BUY ORDERS

Price     Time        Quantity
100.50    10:01:01       100
100.50    10:01:02        50
100.40    10:01:03       200
```

The first order has priority because it arrived earlier at the same price.

---

# Partial Fills

Suppose:

```text
BUY  = 100 shares @ 100
SELL = 40 shares @ 99
```

The engine produces:

```text
TRADE = 40 shares @ 99
```

Remaining:

```text
BUY = 60 shares @ 100
```

This allows the simulation to model realistic order-book behavior.

---

# Analytics Engine

The Python service calculates several metrics.

## VWAP

Volume Weighted Average Price:

```text
VWAP = Σ(Price × Volume) / Σ(Volume)
```

---

## SMA

Simple Moving Average:

```text
SMA = Σ Closing Prices / Number of Periods
```

---

## EMA

Exponential Moving Average gives greater weight to recent prices.

```text
EMA_today =
Price_today × α
+
EMA_yesterday × (1 - α)
```

where:

```text
α = 2 / (N + 1)
```

---

## PnL

Profit and Loss:

```text
PnL = Current Portfolio Value - Initial Portfolio Value
```

---

## Exposure

Exposure measures the value currently committed to a position.

A simplified calculation:

```text
Exposure = Position Quantity × Current Market Price
```

---

## Drawdown

Drawdown measures the decline from a previous portfolio peak.

```text
Drawdown =
(Peak Value - Current Value) / Peak Value
```

---

# Communication

The initial system uses lightweight socket-based communication.

```text
C++ Engine
     │
     │ TCP / Unix Domain Socket
     ▼
Python Analytics
```

The gateway then exposes processed data to clients.

```text
Python / Engine
       │
       ▼
Node.js Gateway
       │
       ├── REST
       │
       └── WebSocket
              │
              ▼
        React Dashboard
```

---

# Wire Format

JSON is used initially because it is:

- Easy to debug.
- Human-readable.
- Easy to inspect.
- Supported by all project languages.
- Simple to integrate.

Example market tick:

```json
{
  "type": "market_tick",
  "symbol": "AAPL",
  "timestamp": 1788867000000,
  "price": 185.50,
  "volume": 100
}
```

Example analytics event:

```json
{
  "type": "analytics_update",
  "symbol": "AAPL",
  "vwap": 185.42,
  "sma": 185.31,
  "ema": 185.38,
  "pnl": 1250.50,
  "exposure": 18550.00,
  "drawdown": 0.021
}
```

---

# API Reference

The Node.js gateway provides the external API.

| Method | Endpoint              | Description          |
| ------ | --------------------- | -------------------- |
| GET    | `/api/health`       | Service health       |
| GET    | `/api/status`       | Engine status        |
| GET    | `/api/market`       | Current market data  |
| GET    | `/api/orderbook`    | Current order book   |
| GET    | `/api/trades`       | Recent trades        |
| GET    | `/api/analytics`    | Current analytics    |
| POST   | `/api/engine/start` | Start simulation     |
| POST   | `/api/engine/stop`  | Stop simulation      |
| POST   | `/api/engine/reset` | Reset engine         |
| GET    | `/api/config`       | Read configuration   |
| PUT    | `/api/config`       | Update configuration |

---

# WebSocket Events

WebSocket endpoint:

```text
/ws
```

Supported event types:

```text
market_tick
trade
order_book
analytics_update
engine_status
error
```

Example:

```json
{
  "event": "trade",
  "data": {
    "trade_id": "TRD-50001",
    "symbol": "AAPL",
    "price": 185.50,
    "quantity": 50
  }
}
```

---

# Configuration

Example environment configuration:

```env
ENGINE_HOST=engine-cpp
ENGINE_PORT=9000

ANALYTICS_HOST=analytics-py
ANALYTICS_PORT=9100

GATEWAY_PORT=8080

WS_PATH=/ws

LOG_LEVEL=info

SIMULATION_TICK_RATE=100

DEFAULT_SYMBOL=AAPL
```

Create a local environment file from the example:

```bash
cp .env.example .env
```

Do not commit `.env` files containing secrets.

---

# Getting Started

## Prerequisites

Install:

- Git
- GCC / G++
- CMake
- Make
- Python 3
- Node.js
- npm
- Docker
- Docker Compose

---

## Clone

```bash
git clone https://github.com/adarsh0707-kumar/Trading-Engine.git
cd Trading-Engine
```

---

## Build C++ Engine

```bash
cd engine-cpp
mkdir -p build
cd build
cmake ..
make -j$(nproc)
```

Or:

```bash
cd engine-cpp
make
```

---

## Run Python Analytics

```bash
cd analytics-py

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python src/main.py
```

---

## Run Node.js Gateway

```bash
cd gateway-node

npm install
npm run dev
```

---

## Run React Dashboard

```bash
cd dashboard-react

npm install
npm run dev
```

The Vite development server normally starts on:

```text
http://localhost:5173
```

---

# Docker

The complete platform can be started using Docker Compose.

```bash
docker compose up --build
```

Run in detached mode:

```bash
docker compose up --build -d
```

View logs:

```bash
docker compose logs -f
```

Stop services:

```bash
docker compose down
```

Remove containers and associated volumes:

```bash
docker compose down -v
```

---

# Testing

Testing is divided into multiple levels.

## Unit Tests

Test individual components:

```text
Order
OrderBook
MatchingEngine
Indicators
Risk Calculations
API Services
React Components
```

## Integration Tests

Validate communication between services:

```text
C++ Engine
     ↓
Python Analytics
     ↓
Node Gateway
```

## End-to-End Tests

Validate the complete pipeline:

```text
Market Tick
    ↓
Matching
    ↓
Trade
    ↓
Analytics
    ↓
API
    ↓
WebSocket
    ↓
Dashboard
```

Run the project's test script:

```bash
./scripts/test.sh
```

---

# Performance

Performance is an important part of this project.

Important metrics include:

- Orders processed per second.
- Trades generated per second.
- Matching latency.
- Average event latency.
- P99 latency.
- Socket throughput.
- Analytics processing rate.
- WebSocket message rate.
- CPU utilization.
- Memory usage.

Example benchmark table:

| Metric           |   Target | Measured |
| ---------------- | -------: | -------: |
| Orders/sec       |    100K+ |      TBD |
| Trades/sec       |     50K+ |      TBD |
| Matching latency |   < 1 ms |      TBD |
| P99 latency      |   < 5 ms |      TBD |
| Memory usage     | < 512 MB |      TBD |

> Benchmark results should always be measured on the actual target machine and documented with test conditions.

---

# Performance Optimization Strategy

The project follows an optimization hierarchy:

```text
1. Correctness
      ↓
2. Profiling
      ↓
3. Identify Bottleneck
      ↓
4. Optimize
      ↓
5. Benchmark
      ↓
6. Regression Test
```

Potential future optimizations include:

- Lock-free structures.
- Memory pools.
- Object reuse.
- Binary protocols.
- Zero-copy messaging.
- Shared memory.
- CPU affinity.
- Cache-aware data structures.
- Batch processing.

The goal is not to optimize prematurely.

> **Build the simple correct system first, measure it, then optimize the actual bottlenecks.**

---

# Observability

The platform should provide structured logs and operational metrics.

Recommended log categories:

```text
ENGINE
ORDERBOOK
MATCHING
TRADE
ANALYTICS
GATEWAY
WEBSOCKET
SYSTEM
ERROR
```

Example:

```text
2026-09-08T10:30:00Z INFO ENGINE simulation_started
2026-09-08T10:30:01Z INFO ORDERBOOK order_added
2026-09-08T10:30:01Z INFO MATCHING order_matched
2026-09-08T10:30:01Z INFO TRADE trade_created
2026-09-08T10:30:01Z INFO ANALYTICS metrics_updated
```

---

# Backpressure

Real-time systems must handle situations where producers generate events faster than consumers can process them.

Potential strategies:

- Bounded queues.
- Message batching.
- Consumer throttling.
- Dropping non-critical market updates.
- Separate critical and non-critical event channels.
- Monitoring queue depth.
- Backpressure propagation.

Trade events should generally receive higher reliability guarantees than high-frequency visualization updates.

---

# Security

Although this is a simulation, security is treated as an engineering requirement.

Security considerations include:

- Input validation.
- Request-size limits.
- Rate limiting.
- Authentication hooks.
- Authorization middleware.
- Secure configuration.
- Secret management.
- Container isolation.
- Dependency scanning.
- Avoiding sensitive data in logs.
- WebSocket connection validation.

The `.env` file should never be committed.

---

# Docker Architecture

A typical deployment contains:

```text
┌───────────────────────────────────────────┐
│              Docker Network               │
│                                           │
│  ┌─────────────┐                          │
│  │ C++ Engine  │                          │
│  └──────┬──────┘                          │
│         │                                  │
│  ┌──────▼──────┐                          │
│  │   Python    │                          │
│  │  Analytics  │                          │
│  └──────┬──────┘                          │
│         │                                  │
│  ┌──────▼──────┐                          │
│  │ Node Gateway│                          │
│  └──────┬──────┘                          │
│         │                                  │
│  ┌──────▼──────┐                          │
│  │    React    │                          │
│  │  Dashboard  │                          │
│  └─────────────┘                          │
│                                           │
└───────────────────────────────────────────┘
```

Docker Compose provides reproducible local environments and simplifies service orchestration.

---

# Architecture Decisions

Important decisions are documented as ADRs.

## ADR-001 — Polyglot Architecture

Use different languages for different workload characteristics:

```text
C++       → Performance-critical engine
Python    → Quantitative analytics
TypeScript → API / Gateway
React     → Visualization
```

## ADR-002 — Socket IPC

Use TCP or Unix Domain Sockets for initial inter-service communication.

Advantages:

- Simple.
- Easy to debug.
- Language independent.
- Suitable for local and containerized development.

## ADR-003 — JSON Wire Format

Use JSON initially for interoperability and debugging.

A binary protocol such as Protocol Buffers can be introduced after profiling.

## ADR-004 — WebSocket Gateway

Use WebSockets for low-latency dashboard updates while keeping the internal services isolated from browser clients.

## ADR-005 — Docker Compose

Use Docker Compose for local multi-service orchestration.

## ADR-006 — Shared Memory as Future Optimization

Shared memory may be introduced later if profiling shows socket-based IPC to be a meaningful bottleneck.

---

# Roadmap

## Phase 1 — Foundation

- [X] Repository structure
- [X] Documentation structure
- [X] Architecture definition
- [X] Initial ADRs
- [ ] Build infrastructure

## Phase 2 — C++ Engine

- [ ] Order model
- [ ] Order validation
- [ ] Order book
- [ ] Matching engine
- [ ] Market simulator
- [ ] Trade generation
- [ ] Socket server
- [ ] Engine tests

## Phase 3 — Python Analytics

- [ ] Event consumer
- [ ] VWAP
- [ ] SMA
- [ ] EMA
- [ ] PnL
- [ ] Exposure
- [ ] Drawdown
- [ ] Analytics tests

## Phase 4 — Node.js Gateway

- [ ] REST API
- [ ] WebSocket server
- [ ] Service clients
- [ ] Validation
- [ ] Rate limiting
- [ ] Error handling

## Phase 5 — React Dashboard

- [ ] Dashboard layout
- [ ] Market chart
- [ ] Order book
- [ ] Trade feed
- [ ] Analytics cards
- [ ] Engine controls
- [ ] WebSocket integration

## Phase 6 — Integration

- [ ] Docker Compose
- [ ] End-to-end pipeline
- [ ] Integration tests
- [ ] CI/CD
- [ ] Logging
- [ ] Benchmarking

## Phase 7 — Optimization

- [ ] Profiling
- [ ] Performance benchmarks
- [ ] IPC optimization
- [ ] Memory optimization
- [ ] Concurrency improvements
- [ ] Optional shared memory transport

---

# Future Improvements

Potential future capabilities:

### Trading

- Market orders.
- Limit orders.
- Stop orders.
- Stop-limit orders.
- Multiple symbols.
- Multiple accounts.
- Strategy simulation.
- Order cancellation.
- Order modification.

### Matching

- Multi-threaded matching.
- Sharded order books.
- Advanced priority queues.
- Deterministic replay.

### Analytics

- Sharpe ratio.
- Sortino ratio.
- Volatility.
- Beta.
- Alpha.
- Value at Risk.
- Position concentration.
- Realized/unrealized PnL.

### Infrastructure

- Kafka.
- Redis Streams.
- NATS.
- gRPC.
- Protocol Buffers.
- Shared memory.
- Memory-mapped event logs.

### Dashboard

- Strategy controls.
- Historical replay.
- Performance heatmaps.
- Risk dashboards.
- Latency dashboards.
- System health dashboard.

---

# Limitations

This project is a simulation and intentionally does not attempt to reproduce the complete behavior of a real exchange.

Important limitations:

- Market data is simulated.
- No real exchange connectivity.
- No real order execution.
- Simplified transaction costs.
- Simplified risk model.
- Simplified market microstructure.
- No regulatory compliance layer.
- No production-grade financial persistence.

The project should not be used for real-money trading.

---

# Example End-to-End Scenario

Suppose the simulator produces:

```text
AAPL = $185.50
```

A strategy submits:

```text
BUY 100 AAPL @ $185.50
```

Another simulated participant submits:

```text
SELL 40 AAPL @ $185.50
```

The matching engine produces:

```text
TRADE
Quantity = 40
Price    = $185.50
```

The remaining order becomes:

```text
BUY 60 AAPL @ $185.50
```

Python receives the trade event and updates:

```text
VWAP
SMA
EMA
PnL
Exposure
Drawdown
```

The Node.js gateway broadcasts the updated state through WebSocket.

The React dashboard then updates:

```text
Market Price
Order Book
Recent Trades
VWAP
PnL
Exposure
Risk Metrics
```

This creates a complete end-to-end real-time trading simulation.

---

# Git Workflow

Recommended branch structure:

```text
main
│
├── feature/order-book
├── feature/matching-engine
├── feature/analytics
├── feature/gateway
└── feature/dashboard
```

Recommended commit prefixes:

```text
feat:
fix:
docs:
test:
refactor:
perf:
build:
ci:
chore:
```

Examples:

```bash
git commit -m "feat(engine): implement price-time priority matching"

git commit -m "feat(analytics): add VWAP and EMA indicators"

git commit -m "feat(gateway): add WebSocket market stream"

git commit -m "docs(adr): document socket IPC decision"

git commit -m "test(engine): add order book integration tests"
```

---

# Documentation

Detailed documentation is maintained under `docs/`.

```text
docs/
├── 01-product-requirements.md
├── 02-architecture.md
├── 03-data-model.md
├── 04-api-reference.md
├── 05-roadmap-and-phases.md
├── 06-development-guide.md
├── 07-security.md
├── 08-gap-analysis.md
├── 09-testing-strategy.md
├── 10-glossary.md
│
├── diagrams/
│   ├── system-architecture.png
│   ├── data-flow.png
│   ├── service-interaction.png
│   ├── order-book-flow.png
│   └── deployment-architecture.png
│
└── decisions/
    ├── ADR-001-polyglot-architecture.md
    ├── ADR-002-socket-ipc.md
    ├── ADR-003-json-wire-format.md
    ├── ADR-004-websocket-gateway.md
    ├── ADR-005-docker-compose.md
    └── ADR-006-shared-memory-future.md
```

---

# Contributing

Contributions should follow the project's engineering standards.

Before submitting a pull request:

1. Create a feature branch.
2. Implement the change.
3. Add or update tests.
4. Run the test suite.
5. Run formatting and lint checks.
6. Update documentation when required.
7. Create a focused commit.
8. Open a pull request.

Keep changes modular and avoid mixing unrelated features.

---

# License

This project is intended as an educational and portfolio project.

A formal open-source license can be added when the project's distribution terms are finalized.

---

# Author

**Adarsh Kumar**

Cloud-Based Algorithmic Trading Engine

---

# Project Philosophy

The project is built around a simple engineering philosophy:

> **Correctness first. Measure second. Optimize third.**

The architecture intentionally starts with technologies and protocols that are easy to understand, test, debug, and deploy. Performance-critical optimizations such as shared memory, zero-copy communication, lock-free data structures, and binary protocols should be introduced only when benchmarks demonstrate that they provide meaningful benefits.

---

## Final Architecture

```text
                    ┌──────────────────────┐
                    │   Market Simulator   │
                    └──────────┬───────────┘
                               │
                               ▼
              ┌───────────────────────────────┐
              │       C++ Trading Engine      │
              │                               │
              │ Order Book + Matching Engine  │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │      Python Analytics          │
              │                               │
              │ Indicators + Risk + Portfolio  │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │       Node.js Gateway          │
              │                               │
              │ REST API + WebSocket + Auth   │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │        React Dashboard         │
              │                               │
              │ Charts + Order Book + Metrics │
              └───────────────────────────────┘
```

---

**Built as a systems-engineering portfolio project demonstrating C++, Python, TypeScript, React, distributed services, networking, real-time systems, quantitative analytics, testing, Docker, and software architecture.**
