# ADR-003: Use JSON as the Initial Inter-Service Wire Format

- **Status:** Accepted
- **Date:** 2026-09-07
- **Date Adopted:** 2026-09-07
- **Scope:** Service-to-service messaging

---

## 1. Context

The system contains multiple programming languages:

- C++;
- Python;
- TypeScript;
- React/TypeScript.

All services must understand common event structures.

The project requires a message format that is:

- language independent;
- human-readable;
- easy to debug;
- easy to log;
- easy to inspect during development.

---

## 2. Decision

JSON will be used as the initial wire format for MVP communication.

Example:

    {
      "type": "trade",
      "symbol": "SIMBANK",
      "price": 102.45,
      "quantity": 100,
      "timestamp": 1787654321000,
      "sequence": 10042
    }

All messages must conform to schemas stored in:

    shared/schemas/

---

## 3. Message Requirements

Every event should contain sufficient metadata for:

- identification;
- ordering;
- debugging;
- observability.

Recommended common fields:

| Field | Purpose |
|---|---|
| type | Event type |
| version | Protocol version |
| sequence | Ordering |
| timestamp | Event time |
| symbol | Instrument |
| payload | Event-specific data |

---

## 4. Advantages

JSON provides:

- human readability;
- simple implementation;
- easy logging;
- easy browser compatibility;
- native support across languages;
- simple debugging.

A developer can inspect a raw event without specialized tools.

---

## 5. Alternatives Considered

### Protocol Buffers

Advantages:

- compact binary representation;
- schema enforcement;
- generated code;
- better serialization performance.

Not selected for MVP because it increases initial implementation complexity.

### MessagePack

Provides smaller messages than JSON but reduces readability.

### XML

Rejected because it is unnecessarily verbose for this system.

---

## 6. Schema Management

JSON schemas will be version-controlled.

Example:

    shared/
    └── schemas/
        ├── tick.schema.json
        ├── order.schema.json
        ├── trade.schema.json
        └── analytics.schema.json

Schema changes must maintain backward compatibility where practical.

---

## 7. Performance Consideration

JSON is not expected to be the final highest-performance protocol.

The system will first establish correctness and measure actual throughput.

If serialization becomes a bottleneck, Protocol Buffers can replace JSON without changing the logical event model.

---

## 8. Consequences

### Positive

- Fast development.
- Excellent observability.
- Easy debugging.
- Easy cross-language integration.

### Negative

- Larger messages.
- Parsing overhead.
- Less efficient than binary protocols.

---

## 9. Future Migration

Potential future architecture:

    C++ ── gRPC/Protobuf ── Python
               |
               ↓
        Internal binary protocol

The public WebSocket API may continue using JSON because browser clients benefit from human-readable messages.