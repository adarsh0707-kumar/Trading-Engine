# Contributing to Cloud-Based Algorithmic Trading Engine

Thank you for your interest in contributing to the **Cloud-Based Algorithmic Trading Engine**.

This project is a portfolio-grade, polyglot, distributed trading simulation platform designed to demonstrate concepts used in modern trading infrastructure, including:

- High-performance C++ order matching
- Market data processing
- Python financial analytics
- Node.js/TypeScript API services
- WebSocket-based real-time communication
- React/TypeScript dashboards
- Inter-process communication
- Docker-based orchestration
- Automated testing and CI/CD
- Performance engineering

We welcome contributions including bug fixes, new features, performance improvements, tests, documentation, refactoring, and architectural improvements.

---

## 1. Project Architecture

The platform follows this high-level architecture:

```text
                    ┌─────────────────────────┐
                    │    React Dashboard      │
                    │    TypeScript / Vite    │
                    └────────────┬────────────┘
                                 │
                           REST / WebSocket
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     Node.js Gateway     │
                    │       TypeScript        │
                    └────────────┬────────────┘
                                 │
                            IPC / Stream
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    Python Analytics     │
                    │                         │
                    │ VWAP / SMA / EMA / PnL  │
                    │ Position / Risk Metrics │
                    └────────────┬────────────┘
                                 │
                            IPC / Stream
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      C++ Engine         │
                    │                         │
                    │ Market Data             │
                    │ Order Book              │
                    │ Matching Engine         │
                    │ Trade Generation        │
                    └─────────────────────────┘
```

### Service Responsibilities

| Component | Technology | Responsibility |
|---|---|---|
| `engine-cpp` | C++17 | Order book, matching engine, market simulation |
| `analytics-py` | Python 3 | VWAP, SMA, EMA, PnL, risk analytics |
| `gateway-node` | Node.js + TypeScript | REST API, WebSocket, routing |
| `dashboard-react` | React + TypeScript | Real-time trading dashboard |
| `shared` | JSON Schemas | Cross-service contracts |
| `docs` | Markdown | Architecture and technical documentation |

---

# 2. Repository Structure

```text
trading-engine/
├── engine-cpp/
│   ├── src/
│   ├── tests/
│   └── Makefile
│
├── analytics-py/
│   ├── src/
│   ├── tests/
│   └── requirements.txt
│
├── gateway-node/
│   ├── src/
│   ├── tests/
│   └── package.json
│
├── dashboard-react/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── shared/
│   └── schemas/
│
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── TESTING.md
│   ├── CHANGELOG.md
│   ├── diagrams/
│   └── decisions/
│
├── docker-compose.yml
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

---

# 3. Development Requirements

Install the following tools before starting development.

## Required

- Git
- C++17 compiler
- Make and/or CMake
- Python 3
- Node.js
- npm
- Docker
- Docker Compose

## Recommended

- GCC or Clang
- GDB
- Valgrind
- AddressSanitizer
- clang-format
- pytest
- Ruff
- ESLint
- Prettier
- VS Code

---

# 4. Clone the Repository

```bash
git clone https://github.com/adarsh0707-kumar/Trading-Engine.git
cd Trading-Engine
```

Check the current branch:

```bash
git branch
```

Update the repository:

```bash
git fetch origin
git pull origin main
```

---

# 5. Development Workflow

The recommended development workflow is:

```text
Issue
  │
  ▼
Feature Branch
  │
  ▼
Implementation
  │
  ▼
Tests
  │
  ▼
Formatting / Linting
  │
  ▼
Local Validation
  │
  ▼
Commit
  │
  ▼
Push
  │
  ▼
Pull Request
  │
  ▼
Code Review
  │
  ▼
CI
  │
  ▼
Merge
```

---

# 6. Branching Strategy

The `main` branch should remain stable.

Do not develop directly on `main`.

Create a separate branch for each change.

## Feature

```bash
git checkout -b feature/order-book-improvements
```

## Bug Fix

```bash
git checkout -b fix/order-matching-bug
```

## Performance

```bash
git checkout -b perf/matching-engine-optimization
```

## Testing

```bash
git checkout -b test/matching-engine
```

## Documentation

```bash
git checkout -b docs/update-architecture
```

## Refactoring

```bash
git checkout -b refactor/order-book
```

Recommended naming:

```text
<type>/<short-description>
```

Examples:

```text
feature/market-data-generator
feature/websocket-reconnection
fix/partial-fill-calculation
fix/order-book-price-level
perf/order-matching
test/matching-engine
docs/api-reference
refactor/analytics-pipeline
ci/add-sanitizer-workflow
```

---

# 7. General Contribution Rules

Keep changes focused.

A pull request should ideally address one feature, bug, or improvement.

Avoid combining unrelated changes:

```text
Feature
+
Unrelated refactoring
+
Large formatting changes
+
Unrelated documentation
```

Prefer:

```text
Feature
+
Required tests
+
Required documentation
```

---

# 8. C++ Engine Contributions

The C++ engine is the performance-critical part of the platform.

Location:

```text
engine-cpp/
```

The engine is responsible for:

```text
Market Data
     │
     ▼
Order Validation
     │
     ▼
Order Book
     │
     ▼
Matching Engine
     │
     ▼
Trade / Fill Events
     │
     ▼
IPC Output
```

---

## 8.1 Price-Time Priority

The matching engine must preserve price-time priority.

For buy orders:

```text
Higher price
     ↓
Earlier timestamp
```

For sell orders:

```text
Lower price
     ↓
Earlier timestamp
```

---

## 8.2 Partial Fills

The engine must support partial order execution.

Example:

```text
Buy Order:
Quantity = 100

Sell Order:
Quantity = 40

Executed:
40

Remaining Buy Quantity:
60
```

---

## 8.3 Order Matching Rules

A buy order can match when:

```text
Buy Price >= Best Ask
```

A sell order can match when:

```text
Sell Price <= Best Bid
```

The implementation must correctly handle:

- Full fills
- Partial fills
- Multiple price levels
- Multiple orders at the same price
- Empty books
- Large orders
- Market orders
- Limit orders
- Order cancellation
- Invalid orders

---

# 9. C++ Testing

Every change to core matching logic should include tests.

Example:

```bash
cd engine-cpp
make test
```

If using CMake:

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build
```

Important test cases include:

```text
Order creation
Order validation
Order cancellation
Order modification
Order book insertion
Price priority
Time priority
Market orders
Limit orders
Partial fills
Full fills
Multiple price levels
Empty order book
Invalid orders
Trade generation
```

---

# 10. C++ Memory Safety

The C++ engine should be tested with memory-safety tools.

AddressSanitizer:

```bash
-fsanitize=address,undefined
```

Example:

```bash
g++ -fsanitize=address,undefined ...
```

Valgrind:

```bash
valgrind --leak-check=full ./build/trading-engine
```

Contributions must not introduce:

- Memory leaks
- Use-after-free
- Buffer overflows
- Undefined behavior
- Invalid memory access

---

# 11. Python Analytics Contributions

Python analytics are located in:

```text
analytics-py/
```

The service consumes trading events and calculates derived metrics.

Typical analytics include:

```text
VWAP
SMA
EMA
PnL
Position
Drawdown
Exposure
Risk Metrics
Trade Statistics
```

---

## 11.1 Python Environment

Create a virtual environment:

```bash
cd analytics-py

python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

---

# 12. Financial Calculation Accuracy

Financial calculations must be implemented carefully.

Avoid relying on floating-point equality for monetary values.

For example:

```python
0.1 + 0.2
```

should not be assumed to be exactly:

```python
0.3
```

Where appropriate, use:

```text
Decimal
Integer price representation
Integer quantity representation
```

or another explicitly documented representation.

Tests should cover:

```text
Zero volume
Zero price
Large quantities
Large prices
Fractional quantities
Empty datasets
Missing data
Out-of-order events
Repeated events
```

---

# 13. Node.js / TypeScript Contributions

The gateway is located in:

```text
gateway-node/
```

The gateway is responsible for:

```text
REST API
WebSocket connections
Authentication
Rate limiting
Request validation
Event broadcasting
Connection management
Error handling
```

Install dependencies:

```bash
cd gateway-node
npm install
```

Run development mode:

```bash
npm run dev
```

Build:

```bash
npm run build
```

Test:

```bash
npm test
```

Lint:

```bash
npm run lint
```

---

# 14. API Guidelines

API endpoints should:

- Validate incoming data
- Return appropriate HTTP status codes
- Use consistent response structures
- Avoid exposing internal errors
- Provide useful error messages
- Document breaking changes

Example success response:

```json
{
  "success": true,
  "data": {}
}
```

Example error response:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_ORDER",
    "message": "Order quantity must be greater than zero"
  }
}
```

---

# 15. WebSocket Guidelines

WebSocket communication is used for real-time events.

Example:

```json
{
  "type": "trade.executed",
  "version": 1,
  "timestamp": "2026-09-07T18:00:00Z",
  "data": {
    "symbol": "AAPL",
    "price": 225.50,
    "quantity": 100
  }
}
```

WebSocket events should be:

```text
Explicit
Versioned
Documented
Validated
Backward-compatible where possible
```

Avoid unnecessarily large messages.

---

# 16. React Dashboard Contributions

The dashboard is located in:

```text
dashboard-react/
```

The dashboard should provide real-time visualization of the trading engine.

Expected components include:

```text
Live Price Chart
Order Book
Recent Trades
VWAP
SMA
EMA
PnL
Position
Risk Metrics
Engine Status
Engine Controls
```

Install dependencies:

```bash
cd dashboard-react
npm install
```

Start development server:

```bash
npm run dev
```

Build:

```bash
npm run build
```

---

# 17. UI Guidelines

The dashboard should be:

- Responsive
- Accessible
- Fast
- Consistent
- Easy to understand

Avoid excessive animations that could negatively affect real-time rendering.

Prefer reusable components instead of duplicated UI logic.

---

# 18. Shared Schemas

Cross-service contracts are maintained under:

```text
shared/schemas/
```

Example:

```text
shared/
└── schemas/
    ├── order.schema.json
    ├── trade.schema.json
    ├── market-data.schema.json
    ├── analytics.schema.json
    └── error.schema.json
```

When modifying a message format:

1. Update the schema.
2. Update the producer.
3. Update the consumer.
4. Update tests.
5. Update documentation.
6. Consider backward compatibility.

Never silently change a shared message format.

---

# 19. Inter-Process Communication

The current architecture uses socket-based communication between services.

```text
C++ Engine
     │
     │ Socket Stream
     ▼
Python Analytics
     │
     │ Analytics Stream
     ▼
Node.js Gateway
     │
     │ WebSocket
     ▼
React Dashboard
```

IPC changes must consider:

- Connection failures
- Malformed messages
- Partial reads
- Disconnects
- Timeouts
- Backpressure
- Message validation
- Reconnection

Performance-sensitive IPC changes should include benchmarks.

---

# 20. Docker Development

The complete system can be started using Docker Compose.

From the repository root:

```bash
docker compose up --build
```

Run in detached mode:

```bash
docker compose up -d --build
```

View logs:

```bash
docker compose logs -f
```

View a specific service:

```bash
docker compose logs -f engine-cpp
```

Stop services:

```bash
docker compose down
```

Remove volumes:

```bash
docker compose down -v
```

Do not commit local Docker volumes or generated container data.

---

# 21. Environment Variables

Never commit secrets.

Use:

```text
.env
```

for local configuration.

Provide an example file:

```text
.env.example
```

Example:

```env
NODE_ENV=development

GATEWAY_PORT=3000

ANALYTICS_PORT=8000

ENGINE_HOST=localhost

ENGINE_PORT=9000
```

Never commit:

```text
API keys
Passwords
Tokens
Private keys
Cloud credentials
Production credentials
Database credentials
```

---

# 22. Code Style

Follow the existing style of each language.

---

## C++

Use:

```text
C++17
```

Prefer:

```text
RAII
const correctness
smart pointers
strong types
small functions
clear ownership
```

Avoid unnecessary:

```text
raw owning pointers
global mutable state
magic numbers
uncontrolled macros
```

---

## Python

Follow:

```text
PEP 8
```

Prefer:

```text
Type hints
Small functions
Clear naming
Docstrings for public APIs
Explicit error handling
```

---

## TypeScript

Prefer:

```text
Strict TypeScript
Interfaces
Types
Explicit API contracts
Small modules
async/await
```

Avoid:

```typescript
any
```

unless there is a documented reason.

---

## React

Prefer:

```text
Functional components
Hooks
Reusable components
Typed props
Clear state ownership
```

Avoid unnecessary global state.

---

# 23. Formatting and Linting

Before opening a pull request, run the appropriate formatters and linters.

Node.js:

```bash
npm run lint
```

Python:

```bash
ruff check .
```

C++:

```bash
clang-format
```

Formatting and linting commands may differ between services.

Always follow the configuration present in the repository.

---

# 24. Testing Requirements

Contributions should include tests whenever applicable.

### Bug Fix

Add a regression test reproducing the bug.

### New Feature

Add appropriate:

```text
Unit tests
Integration tests
```

### Performance Change

Include:

```text
Benchmark
Before/after comparison
```

### API Change

Include:

```text
Request validation tests
Response tests
Error tests
```

---

# 25. Testing Strategy

The project follows a testing pyramid:

```text
                  ┌───────────────┐
                  │ System Tests  │
                  └───────┬───────┘
                          │
                  ┌───────▼───────┐
                  │ Integration   │
                  │    Tests      │
                  └───────┬───────┘
                          │
                ┌─────────▼─────────┐
                │    Unit Tests     │
                └───────────────────┘
```

Most business logic should be covered by unit tests.

---

# 26. Commit Messages

Use clear and descriptive commit messages.

Recommended format:

```text
<type>: <description>
```

Common types:

```text
feat
fix
perf
test
docs
refactor
build
ci
chore
```

Examples:

```text
feat: add price-time priority matching
fix: handle partial order fills
perf: optimize order book lookup
test: add matching engine edge cases
docs: update architecture documentation
refactor: simplify trade event serialization
build: improve docker build configuration
ci: add sanitizer workflow
```

Avoid:

```text
update
changes
fix
final
done
new code
```

---

# 27. Pull Requests

Before opening a pull request:

```bash
git status
```

Review your changes:

```bash
git diff
```

Run all relevant tests.

Then verify:

```bash
git status
```

Push the branch:

```bash
git push -u origin feature/your-feature
```

Open a pull request against:

```text
main
```

---

# 28. Pull Request Description

A pull request should contain:

## Summary

What changed?

## Motivation

Why was the change necessary?

## Testing

How was the change tested?

## Performance

Does the change affect performance?

## Breaking Changes

Does the change modify an API, schema, protocol, or existing behavior?

Example:

```markdown
## Summary

- Added price-time priority matching
- Added partial-fill support
- Added matching engine tests

## Testing

- `make test`
- AddressSanitizer
- Valgrind

## Performance

No measurable regression in the existing benchmark.

## Breaking Changes

None.
```

---

# 29. Architecture Changes

Major architectural decisions should be documented using ADRs.

Location:

```text
docs/decisions/
```

Example:

```text
docs/decisions/
├── ADR-001-polyglot-architecture.md
├── ADR-002-socket-ipc.md
├── ADR-003-json-wire-format.md
├── ADR-004-websocket-gateway.md
├── ADR-005-docker-compose.md
└── ADR-006-shared-memory-future.md
```

Create a new ADR when changing:

```text
Communication protocols
Data formats
Service boundaries
Database strategy
Deployment architecture
Performance architecture
Major dependencies
Security architecture
```

---

# 30. Performance Contributions

Performance is especially important for the C++ matching engine.

Do not optimize based only on assumptions.

Use:

```text
Measure
   │
   ▼
Identify Bottleneck
   │
   ▼
Optimize
   │
   ▼
Benchmark
   │
   ▼
Compare
   │
   ▼
Document
```

Example:

```text
Before:
1.2M orders/sec

After:
1.8M orders/sec

Improvement:
+50%
```

Correctness must never be sacrificed for insignificant performance gains.

---

# 31. Security

If you discover a security vulnerability, avoid publishing sensitive details publicly in an issue.

Report security concerns privately to the project maintainer.

Never commit:

```text
Credentials
Secrets
Private keys
Access tokens
Production configuration
```

Security-related changes should receive additional review.

---

# 32. Issues

Before creating an issue, search existing issues first.

A useful issue should contain:

```text
Description
Expected behavior
Actual behavior
Steps to reproduce
Environment
Relevant logs
Screenshots when useful
Minimal reproduction
```

For performance issues, include:

```text
Hardware
Compiler version
Build configuration
Dataset size
Benchmark results
```

---

# 33. Feature Requests

Feature requests should explain:

```text
Problem
Proposed solution
Alternative solutions
Expected benefit
Potential architectural impact
```

Possible future features include:

```text
Kafka market-data transport
gRPC / Protobuf protocol
Shared-memory ring buffer
Redis event cache
Kubernetes deployment
Prometheus metrics
OpenTelemetry tracing
Distributed load testing
Advanced risk engine
Historical market replay
```

---

# 34. Documentation Contributions

Documentation is considered part of the project.

Documentation contributions may include:

```text
README
Architecture
API reference
Developer guide
Testing guide
Installation guide
ADR
Changelog
Diagrams
Examples
```

Keep documentation synchronized with the implementation.

Do not document functionality that has not been implemented as though it already exists.

---

# 35. Generated Files

Do not commit generated development artifacts such as:

```text
build/
dist/
node_modules/
__pycache__/
.venv/
coverage/
logs/
*.o
*.a
*.so
*.exe
temporary benchmark output
runtime sockets
PID files
```

These files should be handled by `.gitignore`.

---

# 36. Backward Compatibility

When changing APIs, schemas, or event formats, consider existing consumers.

Possible compatibility strategies:

```text
Version fields
Optional fields
New event types
Migration periods
Schema versioning
```

Avoid breaking existing consumers without documentation.

---

# 37. Review Checklist

Before requesting review:

```text
[ ] Code compiles
[ ] Tests pass
[ ] New behavior has tests
[ ] Existing behavior remains intact
[ ] No secrets were committed
[ ] No generated files were committed
[ ] Formatting is correct
[ ] Linting passes
[ ] Documentation is updated
[ ] API/schema changes are documented
[ ] ADR added if required
[ ] Commit messages are meaningful
[ ] PR description is complete
```

---

# 38. Definition of Done

A contribution is considered complete when:

```text
Implementation
      +
Tests
      +
Documentation
      +
Code Review
      +
CI Validation
      +
No Known Regressions
```

have been completed.

---

# 39. Development Principles

The project follows these principles.

## Correctness First

Trading behavior must be deterministic and correct.

## Measure Before Optimizing

Performance improvements should be supported by measurements.

## Explicit Contracts

Services communicate through documented schemas and protocols.

## Test Critical Logic

Matching, order handling, analytics, and financial calculations require strong test coverage.

## Small Changes

Prefer focused pull requests that are easy to review.

## Production Mindset

Although this is a simulation platform, engineering practices should resemble production trading infrastructure.

## Documentation as Code

Architectural and behavioral changes should be reflected in documentation.

---

# 40. Questions and Discussion

For implementation or architecture questions, open an issue with sufficient context.

For major architectural changes, discuss the proposal before starting implementation.

---

# 41. License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

See:

```text
LICENSE
```

for the applicable license terms.

---

# 42. Thank You

Thank you for contributing to the **Cloud-Based Algorithmic Trading Engine**.

Every contribution helps improve:

```text
Performance
Correctness
Reliability
Maintainability
Documentation
Engineering Quality
```

Happy building! 🚀
