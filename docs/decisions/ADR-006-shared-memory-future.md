# ADR-006: Defer Shared-Memory IPC Until Performance Justifies It

- **Status:** Accepted
- **Date:** 2026-09-07
- **Scope:** High-performance C++ ↔ Python communication

---

## 1. Context

The trading engine may eventually generate a very high volume of events.

Socket communication introduces:

- system calls;
- kernel/network buffering;
- data copying;
- serialization overhead;
- context switching.

Shared memory can reduce some of these costs.

A shared-memory architecture could use:

    C++ Producer
         ↓
    Shared Memory
         ↓
    Ring Buffer
         ↓
    Python Consumer

However, shared memory introduces significant concurrency complexity.

---

## 2. Decision

Shared-memory IPC will NOT be part of the initial MVP.

The project will first use socket communication.

Shared memory will be introduced only if performance measurements demonstrate that socket IPC is a meaningful bottleneck.

---

## 3. Rationale

Premature optimization would increase complexity before the actual bottleneck is known.

The engineering sequence should be:

    Implement
       ↓
    Measure
       ↓
    Profile
       ↓
    Identify bottleneck
       ↓
    Optimize
       ↓
    Measure again

This approach ensures that optimization decisions are based on evidence.

---

## 4. Potential Shared-Memory Design

A future implementation may use a lock-free or low-lock ring buffer.

Conceptually:

    Producer
       │
       ▼
    ┌───────────────────────────┐
    │      Shared Memory        │
    │                           │
    │  [E][E][E][E][ ][ ][ ]    │
    │      ↑           ↑        │
    │     Read        Write     │
    │                           │
    └───────────────────────────┘
              │
              ▼
           Consumer

Where:

- C++ owns the producer side;
- Python owns the consumer side;
- atomic indexes coordinate access;
- bounded capacity prevents unlimited memory growth.

---

## 5. Challenges

A shared-memory implementation must correctly handle:

- synchronization;
- memory ordering;
- producer/consumer races;
- process crashes;
- stale data;
- buffer overflow;
- reader lag;
- lifecycle management.

Incorrect synchronization could result in:

- corrupted messages;
- lost events;
- duplicate events;
- undefined behavior.

---

## 6. Performance Evaluation

Before adopting shared memory, benchmark:

- messages per second;
- average latency;
- p95 latency;
- p99 latency;
- CPU consumption;
- memory consumption;
- dropped events.

Example benchmark:

    Socket IPC
    ──────────
    Throughput: X events/sec
    p99 latency: Y μs

    Shared Memory
    ─────────────
    Throughput: A events/sec
    p99 latency: B μs

Shared memory should only replace sockets if the improvement justifies the added complexity.

---

## 7. Alternatives Considered

### TCP Socket

Selected for MVP.

### Unix Domain Socket

Potential optimization for same-host deployments.

### gRPC/Protobuf

Potential future protocol improvement.

### Redis

Useful when multiple consumers are required, but unnecessary for the initial direct pipeline.

### Kafka

Potential future solution for durable/high-volume event streaming, but excessive for the initial simulation.

---

## 8. Consequences

### Positive

- MVP remains simple.
- Easier debugging.
- Performance optimization is evidence-driven.
- Future optimization path is documented.

### Negative

- MVP will not demonstrate shared-memory IPC.
- Maximum achievable throughput may be lower.
- A future migration will require additional implementation.

---

## 9. Future Status

This ADR should be revisited after the Phase 7 performance benchmarks.

The decision should be changed only if profiling identifies IPC as a significant bottleneck.