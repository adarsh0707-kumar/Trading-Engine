# ADR-002: Use Socket-Based IPC Between C++ and Python

- **Status:** Accepted
- **Date:** 2026-09-07
- **Decision Owners:** Project Engineering
- **Scope:** C++ Engine → Python Analytics communication

---

## 1. Context

The C++ trading engine generates market events and trade results continuously.

The Python analytics service must consume these events without tightly coupling the two processes.

The communication mechanism must:

- support continuous streaming;
- work between separate processes;
- be simple to debug;
- work inside Docker;
- support future distributed deployment;
- avoid unnecessary complexity during the MVP.

---

## 2. Decision

The initial implementation will use socket-based IPC.

The C++ engine will expose a server endpoint.

The Python analytics service will act as a client.

    C++ Engine
         |
         | TCP / Unix Socket
         ↓
    Python Analytics

For local development, Unix domain sockets may be supported.

For containerized deployment, TCP networking will be the default.

---

## 3. Communication Model

The C++ service will:

1. Start the matching engine.
2. Start the socket server.
3. Accept an analytics connection.
4. Process market events.
5. Serialize results.
6. Send messages to the connected client.

Python will:

1. Connect to the C++ endpoint.
2. Read incoming messages.
3. Parse the messages.
4. Validate the payload.
5. Update analytics state.
6. Publish enriched results.

---

## 4. Why Sockets

Sockets were selected because they provide:

- straightforward implementation;
- simple debugging with tools such as `nc`;
- process isolation;
- compatibility with Docker networking;
- easy transition from local IPC to network communication;
- language independence.

A Python client can consume the same stream regardless of whether the C++ service runs locally or in another container.

---

## 5. Alternatives Considered

### Shared Memory

Advantages:

- extremely low latency;
- minimal copying;
- high throughput.

Disadvantages:

- synchronization complexity;
- more difficult debugging;
- lifecycle management;
- platform-specific considerations.

Deferred to a later performance phase.

### HTTP REST

Rejected for continuous streaming because request/response communication introduces unnecessary overhead.

### gRPC

Potential future solution.

Not selected for MVP because the socket implementation is easier to understand and debug while establishing the system architecture.

### Message Broker

Redis/Kafka/RabbitMQ may be introduced later.

Not required for the initial single-consumer architecture.

---

## 6. Failure Handling

The Python service must tolerate:

- connection loss;
- malformed messages;
- partial reads;
- reconnects;
- engine restarts;
- network timeouts.

The protocol must therefore define:

- message boundaries;
- message type;
- timestamp;
- sequence number;
- payload;
- protocol version.

---

## 7. Consequences

### Positive

- Simple MVP implementation.
- Low infrastructure overhead.
- Easy debugging.
- Works naturally with Docker.
- Can evolve toward distributed deployment.

### Negative

- Manual protocol handling.
- Backpressure must be implemented.
- Message framing must be handled carefully.
- Not as feature-rich as gRPC.

---

## 8. Future Migration

If profiling shows that socket communication is a bottleneck, the system may introduce:

    Mode A:
    C++ → TCP Socket → Python

    Mode B:
    C++ → Shared Memory Ring Buffer → Python

The external analytics contract should remain unchanged.