# Gap Analysis

## 1. Purpose

This document compares the current planned MVP with a production-style trading platform.

The objective is not to pretend the project is an exchange. The objective is to clearly identify what has been simplified and what would be required to move toward a production architecture.

---

## 2. Current MVP vs Production

| Area | MVP | Production-style requirement | Gap |
|---|---|---|---|
| Market data | Deterministic mock stream | Real exchange feed | Large |
| Matching | Single-process engine | Highly optimized/isolated engine | Medium |
| Transport | Socket/JSON | Binary protocol / specialized IPC | Medium |
| Analytics | Python worker | Distributed research/strategy platform | Large |
| Persistence | Optional/in-memory | Durable event store | Large |
| Gateway | Single Node instance | Horizontally scalable gateways | Medium |
| Dashboard | Single browser | Multi-user application | Medium |
| Auth | Basic/optional | Enterprise identity | Large |
| Observability | Logs/metrics | Full telemetry stack | Medium |
| Deployment | Docker Compose | Kubernetes/cloud deployment | Large |
| Fault tolerance | Basic reconnect | Stateful recovery/failover | Large |
| Compliance | Not applicable | Extensive controls | Very large |

---

## 3. Performance Gap

The project may be described as "high-performance" only after measurements are produced.

Important benchmark values:

```text
events/sec
orders/sec
matches/sec
p50 latency
p95 latency
p99 latency
CPU utilization
memory usage
```

The benchmark must state:

- hardware,
- compiler,
- optimization flags,
- workload,
- message size,
- test duration.

---

## 4. IPC Gap

### MVP

```text
Socket + JSON
```

### Advanced mode

```text
Shared memory ring buffer
```

### Production possibilities

Depending on requirements:

- shared memory,
- kernel-bypass networking,
- specialized exchange protocols,
- hardware timestamping,
- colocated systems.

The project should not implement these merely for vocabulary. Implement only what can be measured and explained.

---

## 5. Persistence Gap

The MVP can operate in memory.

A production system needs durable state and event history.

Possible future design:

```text
Engine
  ↓
Event Log
  ↓
Consumers
  ├── Analytics
  ├── Persistence
  └── Monitoring
```

A replayable event log would be especially valuable because it enables deterministic recovery and debugging.

---

## 6. Distributed State Gap

A single order book is naturally stateful.

Horizontal scaling requires a partitioning strategy.

Possible approach:

```text
Instrument A -> Engine shard A
Instrument B -> Engine shard B
Instrument C -> Engine shard C
```

Each instrument has one authoritative matching owner.

---

## 7. Reliability Gap

MVP failure model:

```text
process fails -> restart
```

Advanced failure model:

```text
failure
  ↓
detect
  ↓
recover
  ↓
restore state
  ↓
replay events
  ↓
resume
```

This requires durable state and deterministic replay.

---

## 8. Analytics Gap

The MVP calculates basic indicators.

Production analytics could include:

- strategy engines,
- factor models,
- feature pipelines,
- portfolio risk,
- historical backtesting,
- model versioning.

The boundary should remain clear:

```text
execution truth ≠ research hypothesis
```

---

## 9. Security Gap

The MVP can use simple authentication.

Production would require:

- centralized identity,
- RBAC,
- audit trails,
- secrets management,
- encryption,
- network segmentation,
- vulnerability management.

---

## 10. Observability Gap

MVP:

```text
logs + counters
```

Advanced:

```text
OpenTelemetry
Prometheus
Grafana
distributed traces
centralized log aggregation
```

A correlation ID should exist before advanced tooling is introduced.

---

## 11. UI Gap

The dashboard is primarily an observability interface.

A production trading terminal would need:

- robust order-entry workflows,
- keyboard shortcuts,
- order confirmation,
- permissions,
- audit trails,
- connection recovery,
- stale-data indicators,
- precise numerical formatting.

Those features are deliberately outside the MVP.

---

## 12. Testing Gap

MVP:

- unit tests,
- integration tests,
- end-to-end tests.

Production-style:

- deterministic replay,
- property-based tests,
- fuzzing,
- fault injection,
- soak testing,
- performance regression tests,
- chaos testing.

---

## 13. Cloud Gap

Docker Compose proves reproducibility but not cloud scalability.

A future cloud deployment could include:

```text
Ingress
  ↓
Gateway replicas
  ↓
Message broker
  ↓
Analytics workers
  ↓
Persistent event store
```

The stateful matching engine requires special placement and lifecycle management.

---

## 14. Priority Matrix

### P0 — Required for MVP

- Correct matching.
- Deterministic simulation.
- Valid event schema.
- Analytics.
- WebSocket streaming.
- Dashboard.
- Docker Compose.
- Tests.

### P1 — Strong portfolio improvements

- Structured logging.
- Correlation IDs.
- Benchmarks.
- Failure recovery.
- API authentication.
- Better test coverage.

### P2 — Advanced

- Protobuf.
- gRPC.
- Redis Streams.
- Shared memory.
- Persistent event log.
- Prometheus/Grafana.

### P3 — Research/production simulation

- Multi-instrument sharding.
- Replay engine.
- fault injection.
- Kubernetes.
- distributed tracing.
- strategy plugins.

---

## 15. Key Interview Message

The strongest explanation is not:

> "I built a real high-frequency trading engine."

It is:

> "I built a deterministic trading simulation that separates a C++ matching engine, Python analytics pipeline, Node real-time gateway, and React dashboard. I measured the bottlenecks and used the project to study IPC, event contracts, backpressure, and distributed-service design."

That statement is technically accurate and demonstrates engineering maturity.
