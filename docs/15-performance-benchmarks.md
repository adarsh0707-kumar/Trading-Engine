# Performance Benchmarks

## Cloud-Based Algorithmic Trading Engine

**Document:** 15 - Performance Benchmarks
**Project:** Cloud-Based Algorithmic Trading Engine
**Phase:** Phase 1 - C++ Matching Engine
**Benchmark Phase:** Phase 1.15
**Author:** Adarsh Kumar
**Status:** Completed
**Last Updated:** September 8, 2026

---

# 1. Overview

This document defines the performance benchmarking strategy for the Cloud-Based Algorithmic Trading Engine.

The primary objective of performance benchmarking is to establish a reproducible baseline for the C++ matching engine before further optimization or progression into subsequent development phases.

Phase 1.15 introduces the first automated performance benchmark for the matching engine.

The benchmark focuses on representative order-book scenarios rather than synthetic microbenchmarks of individual functions.

The current benchmark measures:

* Order construction
* Order-book insertion
* Price-level management
* Matching
* Trade creation
* Partial fills
* Automatic GTC order resting
* Order-book cleanup
* Scenario-level execution time

The benchmark intentionally does not modify the matching-engine implementation for optimization purposes. The objective of Phase 1.15 is to establish a trustworthy baseline.

---

# 2. Performance Objectives

The trading engine is intended to evolve into a high-performance trading-system simulation.

Performance benchmarking therefore provides a quantitative baseline for:

1. Matching latency
2. Matching throughput
3. Multi-level order-book traversal
4. Partial-fill processing
5. Order-book maintenance overhead
6. Future optimization work
7. Regression detection

Performance results must always be interpreted together with correctness results.

A faster matching engine that produces incorrect trades, violates price-time priority, corrupts the order book, or mishandles order state is not considered an improvement.

Therefore:

> Correctness is the first requirement. Performance optimization is performed only after deterministic correctness has been established.

---

# 3. Phase 1.15 Scope

Phase 1.15 introduces:

```text
tests/performance/benchmark_matching_engine.cpp
```

The benchmark is compiled through CMake using:

```cmake
# Phase 1.15 - Performance Benchmark
add_executable(benchmark_matching_engine
    tests/performance/benchmark_matching_engine.cpp
)

target_link_libraries(benchmark_matching_engine
    PRIVATE engine_core
)
```

The benchmark does not introduce an external benchmarking dependency.

It uses:

```cpp
std::chrono::steady_clock
```

for elapsed-time measurement.

This keeps the benchmark:

* Lightweight
* Portable
* Dependency-free
* Easy to build
* Easy to execute locally
* Suitable for the current development stage

---

# 4. Benchmark Scenarios

Phase 1.15 contains three representative scenarios.

## 4.1 Single-Level Full Match

This scenario measures a simple order crossing against a single price level.

Conceptually:

```text
ASK
Price: 100
Quantity: 100

        ↓

Incoming BUY
Price: 100
Quantity: 100

        ↓

FULL MATCH
```

The scenario exercises:

* Order construction
* Order-book insertion
* Best-price lookup
* Price crossing
* Trade creation
* Full fill
* Removal of the resting order
* Removal of the empty price level
* Cleanup

---

## 4.2 Five-Level Full Match

This scenario measures a BUY order consuming liquidity across multiple ask price levels.

Conceptually:

```text
ASK BOOK

101 ── 20
102 ── 20
103 ── 20
104 ── 20
105 ── 20

        ↑
        │
Incoming BUY
Quantity: 100
Price: 105
```

The incoming order consumes multiple price levels.

This scenario exercises:

* Best-price traversal
* Multiple price levels
* Price-time priority
* Multiple trades
* Removal of consumed resting orders
* Removal of empty price levels
* Multi-level matching
* Order-book integrity after traversal

This is intentionally more expensive than the single-level scenario because the engine performs more book traversal and trade processing.

---

## 4.3 Partial Fill + GTC Rest

This scenario validates and measures the Phase 1.12 automatic-resting behavior.

Conceptually:

```text
ASK
Price: 100
Quantity: 50

        ↓

Incoming BUY
Price: 100
Quantity: 100

        ↓

50 FILLED
50 REMAINING

        ↓

GTC ORDER RESTS IN BOOK
```

The scenario exercises:

* Matching
* Partial fill
* Remaining quantity calculation
* Order-state transition
* GTC time-in-force behavior
* Automatic resting
* Reinsertion into the order book

This scenario is important because it measures both matching and the additional order-book operation required to maintain an unfilled GTC order.

---

# 5. Benchmark Configuration

The benchmark executes each scenario:

```text
100,000 iterations
```

per benchmark run.

The benchmark reports:

```text
Benchmark
Operations
Seconds
Operations / second
Nanoseconds / operation
```

The primary latency metric is:

```text
nanoseconds / operation
```

The primary throughput metric is:

```text
operations / second
```

---

# 6. Measurement Methodology

The benchmark uses:

```cpp
std::chrono::steady_clock
```

rather than wall-clock time.

`steady_clock` is appropriate for elapsed-duration measurement because it is monotonic and is not affected by changes to the system wall clock.

Each scenario performs its complete setup and execution sequence for every iteration.

The measured region therefore includes the scenario's complete lifecycle.

This is important when interpreting the results.

The benchmark is **not** a pure measurement of:

```cpp
MatchingEngine::match()
```

alone.

Instead, it represents the cost of a complete representative matching scenario.

The measured work can include:

```text
Order construction
        ↓
Order book insertion
        ↓
Book lookup/traversal
        ↓
Matching
        ↓
Trade creation
        ↓
Order state updates
        ↓
Resting of remaining GTC quantity
        ↓
Cleanup
```

This provides a useful end-to-end engine-operation baseline for the current implementation.

---

# 7. Benchmark Environment

The benchmark was executed locally using the project's C++17/CMake build configuration.

The engine uses:

```text
Language:       C++17
Build system:   CMake
Compiler:       GNU C++
Timing API:     std::chrono::steady_clock
Iterations:     100,000 per scenario
External deps:  None for benchmark
```

The benchmark was executed using a Release-oriented build:

```bash
cmake -S . -B build-release -DCMAKE_BUILD_TYPE=Release
cmake --build build-release
```

The benchmark executable is:

```bash
./build-release/benchmark_matching_engine
```

---

# 8. Baseline Results

The benchmark was executed repeatedly to determine a practical baseline rather than relying on a single run.

## 8.1 Five-Run Baseline

| Scenario                | Average Latency | Approx. Average Throughput |
| ----------------------- | --------------: | -------------------------: |
| Single-level full match |      ~436 ns/op |             ~2.29M ops/sec |
| Five-level full match   |    ~1,778 ns/op |             ~0.57M ops/sec |
| Partial fill + GTC rest |      ~459 ns/op |             ~2.22M ops/sec |

These values are the approximate averages of five consecutive benchmark runs.

The benchmark is intentionally treated as a baseline rather than an absolute hardware-independent performance guarantee.

---

# 9. Individual Benchmark Runs

## 9.1 Run 1

| Scenario                |    ns/op |      ops/sec |
| ----------------------- | -------: | -----------: |
| Single-level full match |   496.35 | 2,014,723.60 |
| Five-level full match   | 1,455.64 |   686,980.98 |
| Partial fill + GTC rest |   365.54 | 2,735,710.38 |

---

## 9.2 Run 2

| Scenario                |    ns/op |      ops/sec |
| ----------------------- | -------: | -----------: |
| Single-level full match |   496.85 | 2,012,681.83 |
| Five-level full match   | 1,829.01 |   546,743.20 |
| Partial fill + GTC rest |   468.92 | 2,132,571.57 |

---

## 9.3 Run 3

| Scenario                |    ns/op |      ops/sec |
| ----------------------- | -------: | -----------: |
| Single-level full match |   390.39 | 2,561,557.89 |
| Five-level full match   | 1,741.13 |   574,341.19 |
| Partial fill + GTC rest |   478.65 | 2,089,212.68 |

---

## 9.4 Run 4

| Scenario                |    ns/op |      ops/sec |
| ----------------------- | -------: | -----------: |
| Single-level full match |   482.73 | 2,071,554.82 |
| Five-level full match   | 1,985.70 |   503,600.05 |
| Partial fill + GTC rest |   496.00 | 2,016,124.15 |

---

## 9.5 Run 5

| Scenario                |    ns/op |      ops/sec |
| ----------------------- | -------: | -----------: |
| Single-level full match |   411.62 | 2,429,396.69 |
| Five-level full match   | 1,878.04 |   532,469.62 |
| Partial fill + GTC rest |   452.39 | 2,210,482.06 |

---

# 10. Performance Interpretation

## 10.1 Single-Level Matching

The single-level benchmark produced an approximate baseline of:

```text
~436 ns/op
~2.29 million operations/sec
```

This represents the relatively simple case where the incoming order consumes liquidity at one price level.

The result establishes the current baseline for a basic full-match scenario.

---

## 10.2 Multi-Level Matching

The five-level benchmark produced an approximate baseline of:

```text
~1,778 ns/op
~0.57 million operations/sec
```

This is substantially more expensive than the single-level scenario.

That difference is expected.

The engine must:

* Inspect multiple price levels
* Process multiple resting orders
* Generate multiple trades
* Update remaining quantities
* Remove consumed orders
* Remove empty price levels
* Continue traversal until the incoming order is filled

Therefore, the multi-level benchmark is a useful indicator of order-book traversal cost.

---

## 10.3 Partial Fill and GTC Resting

The partial-fill scenario produced an approximate baseline of:

```text
~459 ns/op
~2.22 million operations/sec
```

The result demonstrates that the current implementation can perform a partial match and subsequently maintain the remaining GTC order without introducing a large scenario-level overhead relative to the simple single-level benchmark.

The scenario also provides a performance regression point for the automatic-resting behavior introduced in Phase 1.12.

---

# 11. Benchmark Variability

Repeated executions show normal runtime variation.

For example, the single-level benchmark varied between approximately:

```text
390 ns/op
```

and:

```text
497 ns/op
```

across the five recorded runs.

The five-level benchmark varied between approximately:

```text
1,456 ns/op
```

and:

```text
1,986 ns/op
```

The partial-fill benchmark varied between approximately:

```text
366 ns/op
```

and:

```text
496 ns/op
```

This variation is expected in a general-purpose operating-system environment.

Potential sources include:

* CPU frequency scaling
* Operating-system scheduling
* Background processes
* CPU cache state
* Memory allocator behavior
* Thermal conditions
* Process placement
* System load

Consequently, benchmark results should be compared using repeated runs and aggregate statistics rather than a single measurement.

---

# 12. Correctness Validation

Performance results are only considered meaningful when the engine passes its correctness suite.

The Phase 1.15 validation included:

## 12.1 CTest

```text
9/9 tests passed
```

Result:

```text
100% tests passed
```

---

## 12.2 Comprehensive Matching Tests

The matching-engine test suite reported:

```text
All MatchingEngine Phase 1.13 tests passed (34/34)
```

Therefore:

```text
34/34 matching tests passed
```

---

## 12.3 Sanitizer Validation

The previously established sanitizer validation was also successful.

Matching-engine sanitizer result:

```text
34/34 tests passed
```

CTest sanitizer result:

```text
9/9 tests passed
```

This confirms that the benchmark was added without introducing a known correctness or sanitizer regression in the Phase 1 engine.

---

# 13. Benchmark Correctness Requirements

Every future performance benchmark must preserve the following engine invariants.

## 13.1 Price-Time Priority

Orders must continue to match according to:

```text
Best price
    ↓
Earliest sequence/time
```

Performance optimizations must never change matching priority.

---

## 13.2 Trade Price

Trades must continue to execute at the resting order's price.

---

## 13.3 Partial Fills

Partial fills must correctly update:

```text
quantity
remaining quantity
status
```

---

## 13.4 Fully Filled Orders

Fully filled orders must not remain in the active order book.

---

## 13.5 GTC Resting

Unfilled GTC LIMIT orders must remain available in the order book.

---

## 13.6 Order-Book Integrity

After every matching operation:

```text
order_count
price levels
resting orders
remaining quantities
best bid
best ask
```

must remain consistent.

---

# 14. Current Data Structures

The current order book uses:

```text
std::map
```

for price levels.

Bids use descending price ordering:

```text
std::map<double, PriceLevel, std::greater<double>>
```

Asks use ascending price ordering:

```text
std::map<double, PriceLevel, std::less<double>>
```

Each price level uses:

```text
std::deque<std::shared_ptr<Order>>
```

to preserve FIFO ordering.

The current architecture therefore provides:

```text
Price priority
    +
FIFO time priority
```

The Phase 1.15 results establish a baseline for these data structures before any future optimization.

---

# 15. What the Benchmark Does Not Measure

The current Phase 1.15 benchmark does not measure:

* Network latency
* TCP latency
* Unix socket latency
* JSON/NDJSON serialization
* Python analytics latency
* Node.js gateway latency
* WebSocket latency
* React rendering latency
* Database latency
* Redis latency
* Docker networking overhead
* Distributed-system latency
* Multi-threaded contention
* CPU-to-CPU communication
* Kernel-bypass networking
* NIC latency
* Production exchange hardware performance

Those measurements belong to later phases.

---

# 16. Hot-Path Benchmarking

The current benchmark measures a representative scenario rather than only the matching hot path.

A future benchmark may isolate:

```cpp
MatchingEngine::match()
```

to determine the cost of matching itself without including:

* Order allocation
* Initial order construction
* Book setup
* Benchmark cleanup

A dedicated hot-path benchmark becomes especially valuable when optimization begins.

The recommended future methodology is:

```text
Scenario benchmark
        +
Hot-path benchmark
        +
Stress benchmark
        +
Concurrency benchmark
        +
End-to-end benchmark
```

This should be introduced only when the project's performance requirements justify the additional benchmarking infrastructure.

---

# 17. Performance Regression Strategy

Future changes to the matching engine should be evaluated against the Phase 1.15 baseline.

The baseline scenarios are:

```text
1. Single-level full match
2. Five-level full match
3. Partial fill + GTC rest
```

A performance regression investigation should begin when a meaningful change is observed across repeated runs.

A single noisy measurement should not automatically be treated as a regression.

Recommended process:

```text
Code change
    ↓
Correctness tests
    ↓
Sanitizer tests
    ↓
Release build
    ↓
Benchmark
    ↓
Compare against baseline
    ↓
Investigate significant regression
```

---

# 18. Optimization Policy

The Phase 1 implementation should not be optimized solely to improve benchmark numbers.

Optimization must be evidence-driven.

The preferred workflow is:

```text
Measure
   ↓
Profile
   ↓
Identify bottleneck
   ↓
Change implementation
   ↓
Validate correctness
   ↓
Benchmark again
   ↓
Compare
```

Premature optimization is explicitly avoided.

In particular, changes to:

* Containers
* Memory ownership
* Allocation strategy
* Price representation
* Matching traversal
* Order storage
* Trade representation

should only be introduced when supported by profiling or a demonstrated requirement.

---

# 19. Future Optimization Candidates

Potential optimization areas for later phases include:

## 19.1 Allocation Reduction

Investigate repeated allocation of:

```text
Order
Trade
shared_ptr
container nodes
```

when profiling demonstrates allocation overhead.

---

## 19.2 Memory Locality

Evaluate whether the current:

```text
std::map
std::deque
std::shared_ptr
```

combination produces unnecessary cache misses.

---

## 19.3 Price Representation

The current engine uses `double` for price.

Future work may evaluate integer tick representation such as:

```text
price_ticks = price × tick_scale
```

to provide deterministic price comparison and potentially improve performance.

This change must be carefully designed because it affects the data model and API.

---

## 19.4 Container Optimization

Alternative data structures may be evaluated after profiling.

Potential candidates include:

```text
flat_map
custom price-level tree
array-based price ladder
intrusive containers
specialized FIFO queues
```

No replacement should be introduced without correctness and benchmark evidence.

---

## 19.5 Memory Pools

A future high-throughput implementation may investigate:

```text
object pools
arena allocation
custom allocators
recycling
```

for frequently created order and trade objects.

---

# 20. Reproducibility

To reproduce the benchmark:

```bash
cd engine-cpp
```

Configure a Release build:

```bash
cmake -S . -B build-release -DCMAKE_BUILD_TYPE=Release
```

Build:

```bash
cmake --build build-release
```

Run the benchmark:

```bash
./build-release/benchmark_matching_engine
```

Run the correctness suite:

```bash
ctest --test-dir build-release --output-on-failure
```

Run the comprehensive matching tests:

```bash
./build-release/test_matching_engine
```

Expected matching result:

```text
All MatchingEngine Phase 1.13 tests passed (34/34)
```

Expected CTest result:

```text
9/9 tests passed
```

---

# 21. Expected Benchmark Output

The exact numbers may vary by hardware and system load.

The output should contain the three benchmark scenarios and report:

```text
Benchmark                         Ops       Seconds      Ops/sec       ns/op
Single-level full match
Five-level full match
Partial fill + GTC rest
```

The benchmark should be interpreted using repeated executions rather than expecting identical numbers on every run.

---

# 22. Baseline Summary

The established Phase 1.15 baseline is:

| Metric                   |         Baseline |
| ------------------------ | ---------------: |
| Single-level full match  |       ~436 ns/op |
| Single-level throughput  |   ~2.29M ops/sec |
| Five-level full match    |     ~1,778 ns/op |
| Five-level throughput    |   ~0.57M ops/sec |
| Partial fill + GTC rest  |       ~459 ns/op |
| Partial-fill throughput  |   ~2.22M ops/sec |
| Matching tests           |     34/34 passed |
| CTest                    |       9/9 passed |
| Sanitizer matching tests |     34/34 passed |
| Sanitizer CTest          |       9/9 passed |
| Benchmark iterations     | 100,000/scenario |

---

# 23. Phase 1.15 Acceptance

Phase 1.15 is considered complete because:

* [x] Benchmark implementation added
* [x] Three representative scenarios implemented
* [x] 100,000 iterations per scenario
* [x] Release benchmark executed
* [x] Multiple benchmark runs recorded
* [x] Baseline performance established
* [x] Matching correctness verified
* [x] CTest validation completed
* [x] Sanitizer validation completed
* [x] Benchmark build integrated into CMake
* [x] Release build artifacts ignored
* [x] Changes committed
* [x] Changes pushed
* [x] Phase 1.15 merged into `main`

---

# 24. Phase 1 Final Status

With Phase 1.15 completed, the C++ matching-engine implementation has completed the planned Phase 1 development sequence.

The completed Phase 1 scope includes:

```text
Order Model
    ↓
Price-Level Container
    ↓
Order Book
    ↓
Best Bid / Ask
    ↓
Single-Level Matching
    ↓
Partial Fills
    ↓
Cancellation
    ↓
Book Snapshot
    ↓
Deterministic Simulator
    ↓
Simulator Integration
    ↓
Multi-Level Matching
    ↓
Automatic GTC Resting
    ↓
Comprehensive Matching Tests
    ↓
Full Phase Validation
    ↓
Performance Benchmark
```

Phase 1 correctness and performance baselines have therefore been established.

---

# 25. Phase 1 Exit Criteria

The Phase 1 exit criteria are satisfied by the following evidence:

```text
Matching implementation
        ✓

Partial fills
        ✓

Cancellation
        ✓

Multi-level matching
        ✓

Automatic GTC resting
        ✓

Comprehensive matching coverage
        ✓

34/34 matching tests
        ✓

9/9 CTest tests
        ✓

34/34 sanitizer matching tests
        ✓

9/9 sanitizer CTest tests
        ✓

Performance benchmark
        ✓

Performance baseline
        ✓
```

Therefore:

> **Phase 1 — C++ Matching Engine is COMPLETE.**

---

# 26. Transition to Phase 2

Phase 2 should begin only after the Phase 1 baseline is preserved.

The Phase 1.15 benchmark results become the reference point for future performance comparisons.

Future changes should record:

```text
Baseline
    ↓
Optimization
    ↓
New benchmark
    ↓
Performance delta
    ↓
Correctness validation
```

The Phase 1 baseline should not be overwritten.

Instead, future benchmark results should be tracked as historical revisions.

---

# 27. Recommended Next Benchmarking Stages

Future performance work should proceed incrementally.

## Stage 1 — Hot-Path Benchmark

Measure matching with setup and allocation minimized.

```text
MatchingEngine::match()
```

This will provide a more precise engine latency measurement.

---

## Stage 2 — Large Order Book Stress Test

Test progressively larger books:

```text
100 orders
1,000 orders
10,000 orders
100,000 orders
1,000,000 orders
```

Measure:

* Lookup latency
* Matching latency
* Cancellation latency
* Memory usage
* Throughput

---

## Stage 3 — Mixed Workload

Introduce realistic workloads containing:

```text
New orders
Cancels
Partial fills
Full fills
Multi-level matches
Resting orders
```

---

## Stage 4 — End-to-End Benchmark

Eventually measure:

```text
Market Simulator
      ↓
C++ Matching Engine
      ↓
Analytics
      ↓
Node Gateway
      ↓
WebSocket
      ↓
Dashboard
```

This should be performed only after the individual services have stable performance baselines.

---

# 28. Benchmarking Principles

The project follows these performance principles:

1. **Correctness before speed**
2. **Measure before optimizing**
3. **Use repeatable workloads**
4. **Preserve historical baselines**
5. **Profile before changing data structures**
6. **Validate every optimization**
7. **Avoid premature optimization**
8. **Separate microbenchmarks from scenario benchmarks**
9. **Treat operating-system noise as expected**
10. **Never trade deterministic matching correctness for throughput**

---

# 29. Conclusion

Phase 1.15 successfully establishes the first performance baseline for the C++ matching engine.

The current implementation demonstrates approximately:

```text
~2.29M ops/sec
```

for the representative single-level scenario,

```text
~0.57M ops/sec
```

for the representative five-level scenario, and

```text
~2.22M ops/sec
```

for the partial-fill and GTC-rest scenario.

These measurements establish a quantitative reference point for future development.

They should not be interpreted as production-exchange latency figures. The benchmark currently measures complete representative engine scenarios on a general-purpose development machine.

The results provide the necessary baseline for detecting future regressions and evaluating optimization work.

With correctness, sanitizer validation, comprehensive tests, and performance benchmarking completed:

> **Phase 1 — C++ Matching Engine is formally ready to transition to Phase 2.**

---

# 30. Document History

| Version | Date              | Change                                                                             |
| ------- | ----------------- | ---------------------------------------------------------------------------------- |
| 1.0     | September 8, 2026 | Added Phase 1.15 performance benchmark baseline                                    |
| 1.1     | September 8, 2026 | Added repeated-run measurements, validation results, and Phase 1 completion status |

---

**End of Document**
