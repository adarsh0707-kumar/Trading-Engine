# ADR-001: Adopt a Polyglot Service Architecture

- **Status:** Accepted
- **Date:** 2026-09-07
- **Decision Owners:** Project Engineering
- **Scope:** Overall system architecture

---

## 1. Context

The Cloud-Based Algorithmic Trading Engine is designed to simulate the architecture of a modern financial trading platform.

The system must perform several fundamentally different workloads:

1. High-performance order processing and matching.
2. Real-time market-data processing.
3. Financial analytics and risk calculations.
4. Real-time API and WebSocket communication.
5. Interactive browser-based visualization.

No single programming language is equally optimal for all of these responsibilities.

The project therefore requires an architecture that allows each subsystem to use a technology appropriate to its workload while maintaining clear communication contracts between services.

---

## 2. Decision

The system will use a polyglot architecture consisting of four primary services:

| Service | Technology | Primary Responsibility |
|---|---|---|
| Trading Engine | C++17 | Order book and matching |
| Analytics Engine | Python 3 | Market analytics and risk calculations |
| API Gateway | Node.js + TypeScript | API, WebSocket and orchestration |
| Dashboard | React + TypeScript | Real-time visualization |

The architecture is:

    React Dashboard
          |
      WebSocket
          |
    Node.js Gateway
          |
    Analytics Stream
          |
    Python Analytics
          |
        IPC
          |
    C++ Trading Engine

---

## 3. Why C++ for the Trading Engine

The matching engine is the performance-critical component.

C++ provides:

- deterministic execution characteristics;
- low-level memory control;
- efficient data structures;
- predictable resource usage;
- high throughput;
- direct access to POSIX networking primitives;
- compatibility with performance profiling tools.

The order book and matching algorithm will therefore be implemented in C++17.

The project will not claim exchange-grade latency. The goal is to demonstrate the engineering principles used in performance-sensitive systems.

---

## 4. Why Python for Analytics

Python is appropriate for the analytics layer because:

- financial calculations can be developed rapidly;
- NumPy provides efficient numerical operations;
- Python has a large scientific-computing ecosystem;
- analytics logic is expected to change more frequently than the matching engine;
- experimentation is easier than in C++.

Python will handle:

- VWAP;
- SMA;
- EMA;
- volatility;
- simulated PnL;
- drawdown;
- position sizing;
- risk metrics.

---

## 5. Why Node.js for the Gateway

Node.js is well suited to the web-facing layer because it provides:

- efficient asynchronous I/O;
- mature HTTP tooling;
- WebSocket support;
- TypeScript support;
- straightforward integration with React applications.

The Node.js service will isolate browser-facing concerns from the performance-critical C++ engine.

---

## 6. Why React for the Dashboard

React provides:

- component-based UI architecture;
- efficient state-driven rendering;
- TypeScript support;
- mature charting ecosystem;
- straightforward WebSocket integration.

The dashboard will provide:

- live price charts;
- order-book visualization;
- analytics metrics;
- engine controls;
- system status;
- simulated PnL information.

---

## 7. Alternatives Considered

### 7.1 Entire system in C++

Rejected because:

- slower UI development;
- poor fit for browser integration;
- analytics experimentation becomes unnecessarily difficult.

### 7.2 Entire system in Python

Rejected because:

- matching engine would not demonstrate systems-level programming;
- performance characteristics are less suitable for the core simulation;
- weaker demonstration of low-level engineering.

### 7.3 Entire system in Node.js

Rejected because:

- not appropriate for demonstrating a low-level matching engine;
- computationally intensive order-book processing would not showcase the intended systems skills.

### 7.4 Java / Spring Boot

Rejected for this project because the goal is specifically to demonstrate C++ systems programming, Python analytics, and modern JavaScript/React development.

---

## 8. Consequences

### Positive

- Each workload uses an appropriate technology.
- Clear separation of responsibilities.
- Strong portfolio and interview value.
- Individual services can evolve independently.
- Easier future migration to distributed deployment.

### Negative

- More complex development environment.
- Multiple build systems.
- Cross-language data contracts are required.
- Debugging distributed failures is harder.
- Docker orchestration becomes necessary.

---

## 9. Future Evolution

The architecture can later evolve toward:

- gRPC;
- Protocol Buffers;
- Redis or Kafka;
- Kubernetes;
- shared-memory IPC;
- Prometheus/Grafana;
- persistent trade storage.

These upgrades should be introduced only when justified by measurable requirements.