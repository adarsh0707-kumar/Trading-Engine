# Testing Strategy

## 1. Testing Objectives

The testing strategy prioritizes deterministic correctness first and distributed behavior second.

The system contains several classes of risk:

1. Algorithmic errors.
2. Serialization errors.
3. Transport errors.
4. Analytics errors.
5. API contract errors.
6. UI state errors.
7. Deployment/configuration errors.
8. Performance regressions.

---

## 2. Testing Pyramid

```text
                 E2E
                /   \
          Integration
             /       \
       Contract Tests
          /           \
       Unit Tests
```

Most tests should remain fast unit tests.

---

## 3. C++ Unit Tests

### Order validation

Test:

- zero quantity,
- negative/invalid values,
- invalid price,
- unsupported side,
- valid order.

### Order book

Test:

- insert bid,
- insert ask,
- best bid,
- best ask,
- price ordering,
- FIFO ordering.

### Matching

Test:

- exact fill,
- partial fill,
- multiple fills,
- price crossing,
- non-crossing,
- residual quantity,
- FIFO.

---

## 4. Golden Matching Tests

Example:

Input:

```text
S 10 @ 101
S 20 @ 102
B 15 @ 102
```

Expected:

```text
trade 10 @ 101
trade 5  @ 102
remaining ask 15 @ 102
```

Golden tests should compare:

- trade count,
- trade prices,
- quantities,
- remaining orders,
- order status.

---

## 5. Python Unit Tests

### VWAP

Given:

```text
price=100 quantity=10
price=102 quantity=20
```

Expected:

```text
(100*10 + 102*20) / 30
= 101.333333...
```

### SMA

Input:

```text
100, 101, 102
```

Expected:

```text
101
```

### EMA

Verify against a documented reference calculation.

### PnL

Test:

- flat position,
- profitable long,
- losing long,
- short position if supported,
- realized/unrealized transitions.

---

## 6. Contract Tests

Verify that C++ output conforms to the shared event schema.

Verify Python output conforms to the analytics schema.

Verify Node transforms events without dropping required fields.

---

## 7. Socket Tests

Test:

- client connects,
- server accepts,
- complete messages arrive,
- fragmented messages are reconstructed,
- multiple messages arrive in one read,
- disconnect is detected,
- reconnect works,
- malformed input is rejected.

Important principle:

> TCP is a byte stream, not a message protocol.

The application must implement framing.

---

## 8. Node API Tests

Test:

```text
GET /health
GET /simulation/status
POST /simulation/start
POST /simulation/stop
PATCH /simulation/config
GET /metrics/current
```

Verify status codes and JSON structures.

---

## 9. WebSocket Tests

Verify:

- connection,
- initial handshake,
- live event delivery,
- ping/pong,
- invalid messages,
- disconnect,
- reconnect,
- multiple clients.

---

## 10. React Tests

Test:

- connection indicator,
- start/stop controls,
- chart update,
- metrics update,
- stale-data state,
- WebSocket reconnect state,
- empty state,
- error state.

---

## 11. End-to-End Test

The most important scenario:

```text
Start stack
    ↓
Start simulation
    ↓
Generate order
    ↓
Match order
    ↓
Emit trade
    ↓
Calculate analytics
    ↓
Gateway receives event
    ↓
WebSocket broadcasts
    ↓
Dashboard updates
```

The test should assert the event reaches the final consumer.

---

## 12. Failure Tests

Simulate:

- engine restart,
- analytics restart,
- gateway restart,
- temporary socket disconnect,
- malformed event,
- high event rate,
- browser reconnect.

Expected behavior must be documented rather than guessed.

---

## 13. Sanitizers

For C++ development:

```text
AddressSanitizer
UndefinedBehaviorSanitizer
```

Run them regularly.

Look for:

- memory leaks,
- use-after-free,
- buffer errors,
- undefined behavior.

---

## 14. Static Analysis

Possible tools:

```text
clang-tidy
cppcheck
ruff
mypy
ESLint
TypeScript compiler
```

The exact toolchain may be selected based on project dependencies.

---

## 15. Property-Based Testing

Useful order-book invariants:

- quantity never becomes negative,
- filled order has zero remaining quantity,
- cancelled order cannot execute,
- best bid is never above best ask after matching completes,
- total executed quantity equals the sum of fills,
- order IDs remain unique.

---

## 16. Performance Testing

Measure:

```text
throughput
p50 latency
p95 latency
p99 latency
CPU
memory
```

Test multiple workloads:

```text
1k events/sec
10k events/sec
100k events/sec
1M events/sec
```

Only report rates actually achieved.

---

## 17. Soak Testing

Run the complete pipeline for a long duration.

Monitor:

- memory growth,
- connection count,
- event loss,
- latency drift,
- CPU utilization,
- browser stability.

---

## 18. Regression Policy

Every discovered production-like bug should receive a regression test.

Example:

```text
Bug:
same-price FIFO order was reversed.

Fix:
correct queue insertion.

Regression:
test_fifo_same_price().
```

---

## 19. Test Reporting

A release test report should include:

- environment,
- test count,
- passed,
- failed,
- skipped,
- coverage,
- benchmark results,
- known limitations.

---

## 20. Definition of Test Complete

A phase is test-complete when:

- expected behavior has automated coverage,
- failure behavior is understood,
- no known sanitizer errors exist,
- integration contracts pass,
- the documented acceptance criteria pass.
