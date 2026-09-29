# Development Guide

## 1. Development Philosophy

The project is intentionally multi-language, but it should still feel like one coherent product.

Each service should be independently buildable, testable, and runnable.

---

## 2. Repository Layout

```text
trading-engine/
├── engine-cpp/
│   ├── include/
│   ├── src/
│   ├── tests/
│   ├── Makefile
│   └── CMakeLists.txt
├── analytics-py/
│   ├── src/
│   ├── tests/
│   └── requirements.txt
├── gateway-node/
│   ├── src/
│   ├── tests/
│   └── package.json
├── dashboard-react/
│   ├── src/
│   ├── public/
│   └── package.json
├── docker-compose.yml
├── .env.example
└── docs/
```

---

## 3. C++ Development

Recommended standard:

```text
C++17
```

Compiler flags:

```text
-Wall -Wextra -Wpedantic
```

Debug build should include sanitizers where supported:

```text
-fsanitize=address,undefined
```

### C++ design rules

- Prefer RAII.
- Avoid raw ownership.
- Use `std::unique_ptr` where ownership is exclusive.
- Use value types where practical.
- Keep matching logic deterministic.
- Avoid hidden global state.
- Keep I/O separate from business logic.

### Suggested classes

```text
Order
Trade
PriceLevel
OrderBook
MatchingEngine
Simulator
EventSerializer
SocketServer
```

---

## 4. Python Development

Use a virtual environment.

Suggested structure:

```text
analytics-py/
├── src/
│   ├── analytics/
│   │   ├── indicators.py
│   │   ├── pnl.py
│   │   ├── risk.py
│   │   ├── models.py
│   │   └── stream.py
├── tests/
└── requirements.txt
```

### Python rules

- Type annotate public functions.
- Keep calculation functions pure where possible.
- Validate external data.
- Do not let malformed messages terminate the stream processor.
- Separate transport from calculations.

---

## 5. Node.js / Bun Gateway Development

The gateway is implemented in TypeScript and uses Bun as the standard runtime, package manager, test runner, and development toolchain.

### Technology contract

```text
Language       TypeScript
Runtime        Bun
Package manager Bun
HTTP framework Fastify
WebSocket      ws
Validation     Zod
Logging        Pino
Testing        bun test
Metrics        Prometheus-compatible
```

Do not use npm as the default package manager for gateway development. The repository should keep Bun's lockfile as the dependency source of truth.

### Suggested structure

```text
gateway-node/
├── src/
│   ├── server.ts
│   ├── config/
│   ├── api/
│   ├── websocket/
│   ├── clients/
│   ├── services/
│   ├── middleware/
│   ├── observability/
│   └── types/
├── tests/
│   ├── unit/
│   └── integration/
├── package.json
├── tsconfig.json
├── bun.lock
└── Dockerfile
```

Responsibilities:

```text
api            -> HTTP interface
websocket      -> browser streaming
clients        -> C++ engine / analytics connections
services       -> application coordination
middleware     -> validation / errors / security hooks
config         -> typed environment handling
observability  -> logs / metrics
types          -> shared gateway contracts
```

### Gateway design rules

- Use strict TypeScript.
- Keep route handlers thin.
- Keep upstream socket/network logic inside dedicated clients.
- Validate external input before application processing.
- Treat the C++ engine as authoritative for engine/trade state.
- Treat Python Analytics as authoritative for analytics/risk calculations.
- Do not duplicate VWAP, SMA, EMA, PnL, exposure, drawdown, or risk-event calculations in the gateway.
- Keep WebSocket clients isolated from one another.
- Use bounded queues and explicit slow-consumer handling.
- Avoid unhandled promise rejections.
- Close sockets, timers, subscriptions, and servers during shutdown.
- Never log secrets or complete sensitive request payloads.
- Keep REST and WebSocket response contracts typed and documented.

### Bun commands

From gateway-node:

```bash
bun install
bun run dev
bun run build
bun test
bun test --watch
bun run start
```

Exact script names must match package.json once Phase 4.1 is implemented.

### Gateway testing

Use Bun's built-in test runner as the default test command:

```bash
bun test
```

Unit tests should cover configuration, schemas, protocol parsing, event normalization, route behavior, subscription state, errors, and backpressure.

Integration tests should cover:

```text
Gateway ↔ C++ Engine
Gateway ↔ Python Analytics
REST ↔ upstream services
WebSocket ↔ event stream
Reconnect / failure recovery
Graceful shutdown
```

CI must use the same Bun workflow as local development.

## 6. React Development

Use React + TypeScript + Vite.

Suggested structure:

```text
src/
├── app/
├── components/
├── features/
│   ├── market/
│   ├── analytics/
│   ├── orderbook/
│   └── simulation/
├── hooks/
├── services/
├── types/
└── utils/
```

The UI should consume typed event models rather than unstructured `any` objects.

---

## 7. Environment Variables

Use `.env.example`.

Example:

```text
ENGINE_HOST=engine
ENGINE_PORT=7000

ANALYTICS_HOST=analytics
ANALYTICS_PORT=7100

GATEWAY_PORT=8000

VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

Never commit secrets.

---

## 8. Local Development

A practical development sequence is:

### Terminal 1

```bash
cd engine-cpp
make
./build/trading-engine
```

### Terminal 2

```bash
cd analytics-py
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m analytics
```

### Terminal 3

```bash
cd gateway-node
bun install
bun run dev
```

### Terminal 4

```bash
cd dashboard-react
npm install
npm run dev
```

Exact executable and package commands should be aligned with the final repository implementation.

---

## 9. Testing Workflow

### C++

```bash
make test
```

Also run sanitizer builds.

### Python

```bash
pytest
```

### Node / Bun Gateway

```bash
cd gateway-node
bun test
```

### React

```bash
npm test
```

or the selected test runner.

### Full system

```bash
docker compose up --build
```

Then execute an end-to-end test.

---

## 10. Debugging a Broken Pipeline

Trace in this order:

```text
Generator
  ↓
C++ event
  ↓
C++ socket
  ↓
Python parser
  ↓
Python metric
  ↓
Gateway upstream client
  ↓
Gateway WebSocket
  ↓
Browser
```

Use a unique `event_id` to locate one event across logs.

---

## 11. Common Failure Modes

### Connection refused

Check:

- service is running,
- host is correct,
- port is correct,
- container network exists.

### JSON parsing failure

Inspect raw event framing.

A socket stream may split a message across multiple reads. Never assume one `recv()` equals one complete message.

### Browser receives nothing

Check:

1. WebSocket connection.
2. Gateway logs.
3. Analytics output.
4. Engine output.

### Metrics incorrect

Test the calculation independently using a fixed fixture before debugging networking.

---

## 12. Coding Standards

### C++

Allman-style braces are acceptable if consistently applied.

### Python

Use PEP 8-compatible formatting.

### TypeScript

Use strict TypeScript.

### General

- meaningful names,
- small functions,
- explicit errors,
- comments explain why rather than restating what,
- no dead code,
- no secret values in source.

---

## 13. Commit Discipline

Prefer small commits.

Bad:

```text
update everything
```

Good:

```text
feat(engine): add order cancellation
test(engine): cover same-price FIFO ordering
feat(analytics): implement rolling SMA
```

---

## 14. Pull Request Checklist

- [ ] Build passes.
- [ ] Tests pass.
- [ ] No new compiler warnings.
- [ ] Error handling added.
- [ ] API/data contract updated if changed.
- [ ] Documentation updated.
- [ ] Logs remain useful.
- [ ] No credentials committed.
- [ ] Performance impact considered.

---

## 15. Definition of Technical Quality

The project should demonstrate:

- algorithmic correctness,
- systems programming,
- IPC,
- asynchronous programming,
- API design,
- frontend engineering,
- testing,
- containerization,
- observability,
- security awareness.
