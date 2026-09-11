# Trading Engine — Changelog

This document records the development progress, completed milestones, implementation changes, validation results, and planned work for the Trading Engine project.

---

## Status Legend

* ✅ Complete
* 🚧 In Progress
* ⏳ Planned
* ❌ Blocked

---

# Latest Commit Summary

## 2026-09-11 — Unique Trade Identifiers

**Status:** ✅ Complete

`MatchingEngine` derived `trade_id` from the taker and maker order identifiers alone, so the same identifier was emitted whenever a taker matched the same counterparty again or an engine restart reissued order identifiers. Downstream analytics key trades by `trade_id`, so those executions collapsed into one.

### What Changed

* Added a per-engine monotonic trade sequence to `MatchingEngine`
* Changed the trade identifier format to `trade-<sequence>-<taker>-<maker>`
* Added a unit test asserting identifiers stay unique across repeated matches

### Key Files

```text
Modified:
engine-cpp/include/matching/MatchingEngine.hpp
engine-cpp/src/matching/MatchingEngine.cpp
engine-cpp/tests/unit/test_matching_engine.cpp
```

### Validation

```text
ctest (Release)  PASS — 15/15
ctest (Debug)    PASS — 15/15
```

---

## 2026-09-11 — Engine Shutdown and Robustness Fixes

**Status:** ✅ Complete

Three defects found while reviewing the C++ engine (PR #21, PR #23) plus the first working CI pipeline (PR #24).

### What Changed

* Made the C++ test suite assert under `NDEBUG` via `tests/TestCheck.hpp`, which unmasked 5 failing Release tests
* Stopped closing socket descriptors while the receive and accept threads could still be using them
* Replaced the heartbeat `sleep_for` with a condition variable so shutdown no longer waits a full heartbeat interval
* Wrapped the `MatchingEngine::match` call in `Engine::run_loop`, so a rejected order is logged instead of terminating the process
* Added `.github/workflows/test.yml`: ctest in Debug and Release, plus the Python analytics suite

### Key Files

```text
Modified:
.github/workflows/test.yml
engine-cpp/include/network/SocketServer.hpp
engine-cpp/src/engine/Engine.cpp
engine-cpp/src/network/ClientConnection.cpp
engine-cpp/src/network/SocketServer.cpp

Added:
engine-cpp/tests/TestCheck.hpp
```

### Validation

```text
ctest (Release)     PASS — 15/15
ctest (Debug)       PASS — 15/15
Python test suite   PASS — 66 passed
GitHub Actions CI   PASS — 7/7 checks
```

---

## 2026-09-10 — Phase 3.4 Socket Ingestion

**Status:** ✅ Complete

The latest commit completes **Phase 3.4 — Socket Ingestion**, connecting the Python analytics service directly to the C++ trading-engine TCP transport.

### What Changed

* Added Python `SocketClient`
* Implemented C++-compatible TCP message framing
* Added 4-byte big-endian payload-length handling
* Added UTF-8 JSON payload decoding
* Added fragmented TCP frame handling
* Added multiple-frame-per-read handling
* Added maximum payload-size protection
* Added invalid UTF-8 validation
* Added connection/disconnection callbacks
* Added optional automatic reconnection
* Added configurable reconnect delay
* Added heartbeat handling
* Added graceful shutdown
* Added socket-client unit tests
* Added deterministic socket integration tests
* Added C++ ↔ Python interoperability validation
* Updated analytics configuration
* Exported socket-ingestion classes through the ingestion package

### Key Files

```text
Modified:
analytics-py/src/analytics/config/settings.py
analytics-py/src/analytics/ingestion/__init__.py
analytics-py/src/analytics/ingestion/socket_client.py

Added:
analytics-py/tests/unit/test_socket_client.py
analytics-py/tests/integration/test_socket_ingestion.py
```

### Validation

```text
Socket integration test       PASS
Full Python test suite        PASS — 66 passed
C++ ↔ Python interoperability PASS
Fragmented frames             PASS
Multiple frames               PASS
Payload validation            PASS
UTF-8 validation              PASS
Heartbeat                     PASS
Graceful shutdown             PASS
git diff --check              PASS
```

### Result

The end-to-end transport path is now operational:

```text
C++ Trading Engine
        ↓
Trade Generation
        ↓
C++ TCP Transport
        ↓
4-byte Length + UTF-8 JSON
        ↓
Python SocketClient
        ↓
Message Callback
```

### Next Commit Target

**Phase 3.5 — Message Parsing**

The next milestone will convert incoming transport messages into validated Python analytics models and establish the message-processing boundary for the streaming analytics pipeline.

---


# Phase 1 — C++ Matching Engine

## Phase 1 Status

✅ **Complete**

Phase 1 established the core C++ matching-engine functionality.

### Completed Work

* Order model implemented
* Order-side handling
* Price-level container
* Order insertion
* Best bid calculation
* Best ask calculation
* Order matching
* Trade generation
* Matching-engine integration
* Unit tests
* Integration tests
* Sanitizer validation
* Build-system integration
* Documentation updates

### Matching Engine Flow

```text
Incoming Order
      ↓
Order Validation
      ↓
Order Book
      ↓
Price-Level Selection
      ↓
Matching
      ↓
Trade Generation
      ↓
Book Update
```

### Validation

* Matching-engine tests passed
* Integration tests passed
* Sanitizer checks completed
* Core order-book behavior validated

### Phase 1 Exit Criteria

✅ Order model implemented
✅ Price-level management implemented
✅ Add-order functionality implemented
✅ Best bid/ask implemented
✅ Matching implemented
✅ Trade generation implemented
✅ Tests passing
✅ Sanitizer validation completed

---

# Phase 2 — C++ TCP Transport

## Phase 2 Status

✅ **Complete**

Phase 2 added the C++ TCP transport layer required to expose trading-engine events to external services.

### Phase 2 Objectives

* TCP server
* Client connection management
* Message framing
* JSON serialization
* Heartbeat/liveness
* Reconnection support
* Graceful shutdown
* Raw TCP verification
* Protocol documentation

All Phase 2 objectives have been completed.

---

## Phase 2.1 — C++ Transport Server

### Status

✅ **Complete**

Implemented the TCP server responsible for accepting connections from downstream consumers.

### Completed

* TCP listening socket
* Port configuration
* Client accept loop
* Connection lifecycle management
* Transport integration with the C++ engine
* Build-system integration

---

## Phase 2.2 — Client Connection Handling

### Status

✅ **Complete**

Implemented client connection management.

### Completed

* Client registration
* Client disconnection handling
* Per-client connection state
* Connection cleanup
* Safe socket ownership
* Client lifecycle logging

---

## Phase 2.3 — Heartbeat / Liveness

### Status

✅ **Complete**

Implemented heartbeat support for monitoring TCP client liveness.

### Completed

* Heartbeat messages
* Heartbeat request/response handling
* Liveness tracking
* Timeout handling
* Connection health monitoring

### Validation

* Dedicated heartbeat tests passed
* Manual TCP validation passed

### Merge

* Commit: `66d8de7`
* Pull Request: `#17`

---

## Phase 2.4 — Message Framing

### Status

✅ **Complete**

Implemented deterministic TCP message framing.

### Wire Protocol

Each message is transmitted as:

```text
4-byte unsigned payload length
          ↓
Big-endian byte order
          ↓
UTF-8 JSON payload
```

### Completed

* 4-byte payload-length prefix
* Big-endian encoding
* Payload boundary detection
* Partial TCP frame handling
* Multiple frames in a single read
* Deterministic frame parsing

---

## Phase 2.5 — JSON Serialization

### Status

✅ **Complete**

Implemented JSON serialization for transport messages.

### Completed

* JSON message generation
* Message type field
* Request identifiers
* Timestamp fields
* Trade payload serialization
* Heartbeat serialization
* Transport-compatible JSON structure

---

## Phase 2.6 — Reconnection

### Status

✅ **Complete**

Implemented client reconnection support.

### Completed

* Connection failure detection
* Reconnection attempts
* Configurable reconnect behavior
* Reconnect delay
* Connection state reset
* Safe reconnection lifecycle

---

## Phase 2.7 — Graceful Shutdown

### Status

✅ **Complete**

Implemented safe transport shutdown.

### Completed

* Server shutdown
* Client disconnect
* Socket cleanup
* Thread cleanup
* Idempotent shutdown behavior
* Resource cleanup

---

## Phase 2.8 — Raw TCP / `nc` Verification

### Status

✅ **Complete**

Verified the transport protocol independently using raw TCP tooling.

### Validation

* TCP connection established
* Framed messages transmitted
* JSON payload received
* Heartbeat verified
* Connection lifecycle verified

---

## Phase 2 Protocol Documentation

### Status

✅ **Complete**

The protocol documentation now consistently defines:

```text
4-byte big-endian payload length
            +
UTF-8 JSON payload
```

The same framing definition is used by the C++ transport and Python ingestion layers.

---

## Phase 2 Test Results

```text
Total transport tests: 13
Passed:                 13
Failed:                  0

Result: 100% PASS
```

---

# Phase 3 — Python Analytics

## Phase 3 Status

🚧 **In Progress**

Phase 3 introduces the Python analytics service responsible for consuming trading-engine events and producing analytical information.

The Python analytics pipeline is being implemented incrementally.

---

# Phase 3.1 — Python Analytics Foundation

## Status

✅ **Complete**

Established the Python analytics service structure.

### Completed

* Python project structure
* Package configuration
* Analytics package
* Configuration package
* Model package
* Indicator package
* Ingestion package
* Test structure
* Pytest configuration
* Development dependencies
* Basic service configuration

### Project Structure

```text
analytics-py/
├── src/
│   └── analytics/
│       ├── config/
│       ├── indicators/
│       ├── ingestion/
│       ├── models/
│       └── ...
│
└── tests/
    ├── unit/
    └── integration/
```

---

# Phase 3.2 — Analytics Models

## Status

✅ **Complete**

Implemented the initial analytics data models.

### Models

* `Tick`
* `Trade`
* `AnalyticsResult`

### Objectives Completed

* Typed analytical data structures
* Validation
* Serialization compatibility
* Deterministic model behavior
* Unit testing

---

# Phase 3.3 — Streaming Indicators

## Status

✅ **Complete**

Implemented the initial streaming analytics indicators.

### Indicators

* VWAP
* SMA
* EMA
* Volatility

### Completed

* Streaming state management
* Incremental calculations
* Input validation
* Reset behavior
* Deterministic calculations
* Unit tests
* Edge-case handling

### Test / Coverage Status

Before socket ingestion was added:

```text
Tests:                 55
Statements:            182
Missed statements:       1
Coverage:               99%
```

The remaining defensive VWAP branch is intentionally retained because it represents a logically unreachable state under validated inputs.

---

# Phase 3.4 — Socket Ingestion

## Status

✅ **Complete**

**Completion Date:** 2026-09-10

Phase 3.4 implements the Python socket-ingestion layer responsible for consuming events from the C++ trading-engine transport.

The Python analytics service can now communicate directly with the C++ trading engine using the same TCP framing protocol implemented in Phase 2.

---

## Phase 3.4 Objectives

The following objectives have been completed:

* Python TCP socket client
* C++-compatible message framing
* Big-endian payload lengths
* UTF-8 JSON payloads
* Fragmented TCP frame handling
* Multiple frames in a single TCP read
* Maximum payload-size validation
* Invalid UTF-8 detection
* Connection lifecycle callbacks
* Optional automatic reconnection
* Configurable reconnect delay
* Graceful shutdown
* Heartbeat handling
* Deterministic unit tests
* Deterministic integration tests
* C++ ↔ Python interoperability

---

## Socket Client

### File

```text
analytics-py/src/analytics/ingestion/socket_client.py
```

### Main Component

```text
SocketClient
```

The `SocketClient` provides:

* TCP connection management
* Connection timeout
* Receive timeout
* Message callbacks
* Connection callbacks
* Disconnect callbacks
* Optional automatic reconnection
* Configurable reconnect delay
* Graceful shutdown
* Payload-size protection
* Protocol validation
* Heartbeat handling

---

## Wire Protocol

The Python ingestion layer implements the same framing protocol used by the C++ transport.

```text
4-byte unsigned payload length
          ↓
Big-endian byte order
          ↓
UTF-8 JSON payload
```

### Maximum Payload Size

```text
1 MiB
```

Payloads exceeding the configured maximum are rejected.

---

## Configuration

### Updated File

```text
analytics-py/src/analytics/config/settings.py
```

### Environment Variables

```text
TRADING_ENGINE_HOST
TRADING_ENGINE_PORT
TRADING_ENGINE_CONNECT_TIMEOUT
TRADING_ENGINE_RECEIVE_TIMEOUT
TRADING_ENGINE_RECONNECT
TRADING_ENGINE_RECONNECT_DELAY
TRADING_ENGINE_MAX_PAYLOAD_SIZE
```

### Default Endpoint

```text
127.0.0.1:9000
```

---

## Ingestion Package Exports

### Updated File

```text
analytics-py/src/analytics/ingestion/__init__.py
```

Exports:

```text
SocketClient
SocketProtocolError
```

---

## Unit Tests

### File

```text
analytics-py/tests/unit/test_socket_client.py
```

### Coverage Areas

The unit-test suite covers:

* Message framing
* Fragmented frames
* Multiple messages in one read
* Oversized payload rejection
* Invalid UTF-8 detection
* Heartbeat handling
* Sending without an active connection
* Idempotent shutdown
* Socket receive behavior
* Connection lifecycle
* Protocol validation

---

## Integration Tests

### File

```text
analytics-py/tests/integration/test_socket_ingestion.py
```

The integration test implements a deterministic local TCP server using the exact C++ wire protocol.

The test deliberately fragments frames to verify that the Python client correctly reconstructs complete messages.

### Verified Messages

```text
HELLO
TRADE
```

### Dedicated Integration Test

```text
1 passed
```

---

## Full Python Test Suite

After Phase 3.4:

```text
66 passed
```

Result:

```text
PASS
```

---

# Phase 3.4 — C++ ↔ Python Interoperability

## Status

✅ **Complete**

Manual interoperability testing was performed between the C++ trading engine and the Python analytics service.

### C++ Endpoint

```text
127.0.0.1:9000
```

### Python Client

Connected successfully and received:

```text
HELLO
TRADE
HEARTBEAT
```

---

## Example Trade Event

```json
{
  "type": "TRADE",
  "request_id": "trade-SIM-00000171-SIM-00000089",
  "timestamp": "2026-09-10T15:15:02Z",
  "payload": "{\"symbol\":\"SIM\",\"price\":98.57,\"quantity\":3,\"taker_order_id\":\"SIM-00000171\",\"maker_order_id\":\"SIM-00000089\"}"
}
```

### Interoperability Results

* TCP connection established
* HELLO message received
* Trade events received
* Trade structure parsed
* Heartbeat request/response verified
* Graceful shutdown verified
* Disconnect callback verified
* No runtime exceptions observed

---

# Phase 3.4 — End-to-End Ingestion Flow

The completed transport-to-ingestion path is:

```text
C++ Order
      ↓
Order Book
      ↓
Matching Engine
      ↓
Trade Generation
      ↓
C++ TCP Transport
      ↓
4-byte Length + JSON
      ↓
Python SocketClient
      ↓
Message Callback
```

This establishes the foundation for the remaining Python streaming analytics pipeline.

---

# Phase 3.4 — Files Changed

### Modified

```text
analytics-py/src/analytics/config/settings.py
analytics-py/src/analytics/ingestion/__init__.py
analytics-py/src/analytics/ingestion/socket_client.py
```

### Added

```text
analytics-py/tests/integration/test_socket_ingestion.py
analytics-py/tests/unit/test_socket_client.py
```

---

# Phase 3.4 — Validation

```text
Dedicated socket integration test     PASS
Full Python test suite                PASS
C++ ↔ Python interoperability         PASS
Fragmented-frame handling             PASS
Multiple-frame handling               PASS
Payload-size validation               PASS
UTF-8 validation                      PASS
Heartbeat handling                    PASS
Graceful shutdown                     PASS
git diff --check                      PASS
```

---

# Phase 3 Documentation Status

## Status

🚧 **In Progress**

Documentation is being updated continuously as each analytics milestone is completed.

Current documented implementation includes:

```text
Phase 3.1  Python Foundation       ✅
Phase 3.2  Analytics Models        ✅
Phase 3.3  Indicators              ✅
Phase 3.4  Socket Ingestion        ✅
```

---

# Phase 3.5 — Message Parsing

## Status

⏳ **Planned**

Planned work:

* Normalize incoming JSON messages
* Parse `HELLO`
* Parse `TRADE`
* Parse `HEARTBEAT`
* Validate message types
* Convert transport payloads into analytics models
* Handle malformed messages
* Add parser tests

---

# Phase 3.6 — Streaming Processor

## Status

⏳ **Planned**

Planned work:

* Streaming event processor
* Event dispatch
* Trade processing
* Tick processing
* Indicator updates
* Stateful analytics pipeline
* Processing error isolation

---

# Phase 3.7 — Indicator State

## Status

⏳ **Planned**

Planned work:

* Persistent indicator state
* VWAP state
* SMA state
* EMA state
* Volatility state
* Symbol-level state management
* State reset behavior

---

# Phase 3.8 — Position Tracking

## Status

⏳ **Planned**

Planned work:

* Position model
* Position updates
* Buy/sell accounting
* Quantity tracking
* Average entry price
* Symbol-level positions
* Position tests

---

# Phase 3.9 — Realized PnL

## Status

⏳ **Planned**

Planned work:

* Realized profit/loss calculation
* Closed-position accounting
* Trade-to-position reconciliation
* Realized PnL aggregation
* Unit tests

---

# Phase 3.10 — Unrealized PnL

## Status

⏳ **Planned**

Planned work:

* Mark-to-market calculations
* Latest-price tracking
* Open-position valuation
* Unrealized PnL
* Combined PnL calculations

---

# Phase 3.11 — Equity / Drawdown

## Status

⏳ **Planned**

Planned work:

* Equity curve
* Peak equity
* Drawdown calculation
* Maximum drawdown
* Recovery tracking
* Time-series analytics

---

# Phase 3.12 — Risk Management

## Status

⏳ **Planned**

Planned work:

* Position limits
* Exposure limits
* PnL thresholds
* Drawdown thresholds
* Risk events
* Risk-state tracking
* Risk validation tests

---

# Phase 3.13 — Analytics Publisher

## Status

⏳ **Planned**

Planned work:

* Analytics output interface
* Event publishing
* Downstream integration
* Structured analytics messages
* Publisher configuration
* Error handling

---

# Phase 3.14 — Integration Testing

## Status

⏳ **Planned**

Planned work:

* C++ → Python integration tests
* Transport → parser integration
* Parser → analytics integration
* Analytics → publisher integration
* Failure scenarios
* Reconnection scenarios
* Heartbeat scenarios

---

# Phase 3.15 — End-to-End Validation

## Status

⏳ **Planned**

Planned complete flow:

```text
Order
  ↓
Order Book
  ↓
Matching Engine
  ↓
Trade
  ↓
C++ TCP Transport
  ↓
Python Socket Ingestion
  ↓
Message Parser
  ↓
Streaming Processor
  ↓
Indicators
  ↓
Position Tracking
  ↓
PnL
  ↓
Risk
  ↓
Analytics Publisher
```

---

# Phase 3.16 — Performance

## Status

⏳ **Planned**

Planned work:

* Message throughput benchmark
* Parsing benchmark
* Analytics processing benchmark
* Socket ingestion latency
* Memory usage measurement
* CPU usage measurement
* Backpressure evaluation
* Performance regression tests

---

# Phase 3.17 — Production Configuration

## Status

⏳ **Planned**

Planned work:

* Production environment configuration
* Environment variable validation
* Logging configuration
* Runtime configuration
* Connection configuration
* Retry configuration
* Payload limits
* Operational defaults
* Production deployment preparation

---

# Architecture Progress

Current architecture:

```text
                         ┌──────────────────────┐
                         │   C++ Trading Engine │
                         │                      │
Orders ────────────────► │    Order Book        │
                         │         ↓            │
                         │  Matching Engine      │
                         │         ↓            │
                         │    Trade Events       │
                         └──────────┬───────────┘
                                    │
                                    │ TCP
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   C++ TCP Transport  │
                         │                      │
                         │  4-byte BE Length    │
                         │        +             │
                         │    UTF-8 JSON        │
                         └──────────┬───────────┘
                                    │
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Python SocketClient  │
                         │                      │
                         │ Phase 3.4            │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Message Parser     │
                         │     Phase 3.5        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Streaming Processor  │
                         │     Phase 3.6        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Analytics Pipeline   │
                         │   Phases 3.7–3.12    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Analytics Publisher  │
                         │     Phase 3.13       │
                         └──────────────────────┘
```

---

# Completion Criteria

Phase 3 will be considered complete when:

* [x] Python project foundation implemented
* [x] Analytics models implemented
* [x] Streaming indicators implemented
* [x] Socket ingestion implemented
* [ ] Message parsing implemented
* [ ] Streaming processor implemented
* [ ] Indicator state management implemented
* [ ] Position tracking implemented
* [ ] Realized PnL implemented
* [ ] Unrealized PnL implemented
* [ ] Equity and drawdown implemented
* [ ] Risk management implemented
* [ ] Analytics publisher implemented
* [ ] Integration test suite completed
* [ ] End-to-end validation completed
* [ ] Performance benchmarks completed
* [ ] Production configuration completed

---

# Overall Progress Summary

| Phase      | Component                  | Status     |
| ---------- | -------------------------- | ---------- |
| Phase 1    | C++ Matching Engine        | ✅ Complete |
| Phase 2.1  | C++ Transport Server       | ✅ Complete |
| Phase 2.2  | Client Connection Handling | ✅ Complete |
| Phase 2.3  | Heartbeat / Liveness       | ✅ Complete |
| Phase 2.4  | Message Framing            | ✅ Complete |
| Phase 2.5  | JSON Serialization         | ✅ Complete |
| Phase 2.6  | Reconnection               | ✅ Complete |
| Phase 2.7  | Graceful Shutdown          | ✅ Complete |
| Phase 2.8  | Raw TCP Verification       | ✅ Complete |
| Phase 3.1  | Python Foundation          | ✅ Complete |
| Phase 3.2  | Analytics Models           | ✅ Complete |
| Phase 3.3  | Streaming Indicators       | ✅ Complete |
| Phase 3.4  | Socket Ingestion           | ✅ Complete |
| Phase 3.5  | Message Parsing            | ⏳ Planned  |
| Phase 3.6  | Streaming Processor        | ⏳ Planned  |
| Phase 3.7  | Indicator State            | ⏳ Planned  |
| Phase 3.8  | Position Tracking          | ⏳ Planned  |
| Phase 3.9  | Realized PnL               | ⏳ Planned  |
| Phase 3.10 | Unrealized PnL             | ⏳ Planned  |
| Phase 3.11 | Equity / Drawdown          | ⏳ Planned  |
| Phase 3.12 | Risk Management            | ⏳ Planned  |
| Phase 3.13 | Analytics Publisher        | ⏳ Planned  |
| Phase 3.14 | Integration Testing        | ⏳ Planned  |
| Phase 3.15 | End-to-End Validation      | ⏳ Planned  |
| Phase 3.16 | Performance                | ⏳ Planned  |
| Phase 3.17 | Production Configuration   | ⏳ Planned  |

---

# Current Overall Status

## Phase 1

✅ **Complete**

The core C++ matching engine is implemented and validated.

## Phase 2

✅ **Complete**

The C++ TCP transport layer is implemented, tested, documented, and validated.

## Phase 3

🚧 **In Progress**

The Python analytics service has completed:

```text
Phase 3.1 — Python Foundation
Phase 3.2 — Analytics Models
Phase 3.3 — Streaming Indicators
Phase 3.4 — Socket Ingestion
```

The next implementation milestone is:

```text
Phase 3.5 — Message Parsing
```

The remaining Phase 3 analytics, risk, publishing, integration, performance, and production-readiness work remains planned.

---

# Latest Milestone

```text
Date:   2026-09-10
Phase:  Phase 3.4
Task:   Socket Ingestion
Status: ✅ Complete
```

The project now has a validated communication path from the C++ matching engine into the Python analytics service.

```text
C++ Trading Engine
        ↓
C++ TCP Transport
        ↓
Framed JSON Messages
        ↓
Python SocketClient
        ↓
Analytics Pipeline
```

Phase 3.5 — **Message Parsing** is the next development target.

