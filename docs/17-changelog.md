# Trading Engine — Changelog

This document records the implementation progress, completed milestones, important architectural changes, testing status, and remaining work for the Trading Engine project.

The changelog is maintained alongside the roadmap and is intended to provide a reliable project-history and progress reference.

---

## Status Legend

| Status          | Meaning                                                                     |
| --------------- | --------------------------------------------------------------------------- |
| ✅ Complete      | Implemented, tested, documented where applicable, and merged                |
| 🟡 In Progress  | Currently being implemented                                                 |
| ⏳ Pending       | Planned but not yet completed                                               |
| ⚠️ Needs Review | Implemented but requires additional verification, testing, or documentation |
| ❌ Blocked       | Cannot proceed until another dependency is completed                        |

---

# 2026-09-10 — Phase 2 Transport Progress Review

## Current Project Status

The project has completed the C++ order-book foundation and most of the initial C++ transport layer.

### Phase 1 — C++ Order Book

| Component             | Status     |
| --------------------- | ---------- |
| Order model           | ✅ Complete |
| Price-level container | ✅ Complete |
| Add order             | ✅ Complete |
| Best bid / best ask   | ✅ Complete |
| Matching engine       | ✅ Complete |
| Order-book tests      | ✅ Complete |
| Sanitizer validation  | ✅ Complete |
| Phase 1 integration   | ✅ Complete |
| Merge to `main`       | ✅ Complete |

**Phase 1 Status: ✅ Complete**

---

# Phase 2 — C++ Transport

The official roadmap defines Phase 2 as the C++ transport layer.

The current implementation has been internally divided into smaller implementation slices to make development and testing manageable.

## Phase 2 Component Status

| Component                         | Status                              |
| --------------------------------- | ----------------------------------- |
| TCP socket server                 | ✅ Complete                          |
| Client connection handling        | ✅ Complete                          |
| Heartbeat / liveness              | ✅ Complete                          |
| Message framing                   | ✅ Complete                          |
| JSON serialization                | ✅ Complete                          |
| Reconnection behavior             | ⚠️ Needs dedicated integration test |
| Graceful shutdown                 | ⚠️ Needs dedicated verification     |
| Raw TCP debugging with `nc`       | ⏳ Verify                            |
| Phase 2 documentation consistency | ⏳ Pending                           |

### Overall Phase 2 Status

**🟡 Nearly complete**

The core transport implementation is already present. The remaining work is primarily focused on proving reconnect behavior, verifying shutdown behavior, and completing transport documentation.

---

# Phase 2.1 — C++ Transport Server

## Completed

Implemented the TCP transport server with:

* IPv4 loopback socket
* Configurable listening port
* Automatic port allocation using port `0`
* `SO_REUSEADDR`
* TCP listen backlog
* Client acceptance loop
* Connection identifiers
* Client registry
* Client count tracking
* Server start/stop lifecycle
* Broadcast support

### Files

```text
engine-cpp/include/network/SocketServer.hpp
engine-cpp/src/network/SocketServer.cpp
```

### Verification

The network integration tests successfully verify:

* Server starts
* Server obtains a bound port
* Client connects
* Client is registered
* Client receives `HELLO`
* Broadcast messages reach the client

**Status: ✅ Complete**

---

# Phase 2.2 — Client Connection Handling

## Completed

Implemented client-side connection management including:

* TCP socket ownership
* Receive loop
* Send synchronization
* Message callbacks
* Disconnect callbacks
* Socket shutdown
* Socket close
* Connection identifiers
* Error response handling

### Files

```text
engine-cpp/include/network/ClientConnection.hpp
engine-cpp/src/network/ClientConnection.cpp
```

**Status: ✅ Complete**

---

# Phase 2.3 — Heartbeat / Connection Liveness

## Completed

Implemented transport heartbeat handling.

Features include:

* Configurable heartbeat interval
* Configurable heartbeat timeout
* Server heartbeat thread
* `HEARTBEAT` messages
* Heartbeat acknowledgements
* Last heartbeat acknowledgement tracking
* Timeout detection
* Automatic removal of timed-out clients
* Thread-safe heartbeat timestamp access

### Important APIs

```cpp
void markHeartbeatAck();

bool isHeartbeatTimeout(
    std::chrono::seconds timeout) const;

std::chrono::system_clock::time_point
lastHeartbeatAckTime() const;
```

### Tests

Dedicated heartbeat integration coverage includes:

```text
test_heartbeat_sent_and_acked()
test_heartbeat_timeout_disconnects()
```

### Verification

Targeted tests:

```text
test_engine_network .............. Passed
test_connection_heartbeat ........ Passed
```

Full test suite:

```text
13/13 tests passed
100% tests passed
```

### Commit

```text
66d8de7 feat(engine): implement connection heartbeat handling
```

### Merge

Merged into `main` through:

```text
PR #17
```

**Status: ✅ Complete**

---

# Phase 2.4 — Message Framing

## Completed

The transport already implements application-level TCP message framing.

TCP is treated correctly as a byte stream rather than a message protocol.

The current wire format is:

```text
+----------------------+----------------------+
| 4-byte payload size  | JSON payload         |
| big-endian           | UTF-8                |
+----------------------+----------------------+
```

### Protocol Properties

* 4-byte length prefix
* Big-endian integer encoding
* Maximum payload size: 1 MiB
* Partial-frame handling
* Multiple-frame handling
* Complete-frame extraction
* Invalid payload-size rejection

### Files

```text
engine-cpp/include/network/Protocol.hpp
engine-cpp/src/network/Protocol.cpp
```

### Tests

```text
test_protocol_frame()
test_partial_frame()
test_multiple_frames()
```

These tests verify that:

* Complete frames can be encoded and decoded
* Fragmented TCP data can be reconstructed
* Multiple frames in a single read can be extracted correctly

**Status: ✅ Complete**

---

# Phase 2.5 — JSON Serialization

## Completed

The transport uses JSON as the current MVP wire serialization format.

The implementation supports:

* Message → JSON
* JSON → Message
* Message type
* Request ID
* Timestamp
* Payload
* Round-trip validation

### Files

```text
engine-cpp/include/serialization/JsonSerializer.hpp
engine-cpp/src/serialization/JsonSerializer.cpp
engine-cpp/include/serialization/Message.hpp
```

### Tests

```text
test_message_round_trip()
```

Serialization is integrated directly with the network transport.

The current send path is:

```text
Message
   ↓
JsonSerializer
   ↓
JSON
   ↓
Protocol::frame()
   ↓
TCP socket
```

The receive path is:

```text
TCP socket
   ↓
byte buffer
   ↓
Protocol::extractFrame()
   ↓
JSON
   ↓
JsonSerializer
   ↓
Message
```

**Status: ✅ Complete**

---

# Phase 2.6 — Reconnection Behavior

## Current Assessment

The server architecture already supports new connections after a client disconnects.

The accept loop continuously waits for new connections:

```cpp
::accept(...)
```

When a client disconnects:

```text
Client
   ↓
disconnect
   ↓
ClientConnection receive loop detects closure
   ↓
handleDisconnect()
   ↓
client removed from clients_
```

A new client can then connect:

```text
New Client
   ↓
accept()
   ↓
new connection ID
   ↓
ClientConnection
   ↓
HELLO
```

Therefore, a new reconnect mechanism does **not** currently appear necessary.

## Missing Verification

A dedicated integration test still needs to prove:

```text
Client A connects
       ↓
Client A receives HELLO
       ↓
Client A disconnects
       ↓
Server removes Client A
       ↓
Client B reconnects
       ↓
Server accepts Client B
       ↓
Client B receives HELLO
       ↓
Client B can communicate normally
```

### Planned Test

```text
test_client_reconnects()
```

### Expected Verification

The test should confirm:

* First connection succeeds
* First client is registered
* First client receives `HELLO`
* First client disconnects
* Server removes first client
* Second connection succeeds
* Second client receives `HELLO`
* Server remains running
* Second client can exchange messages

**Status: ⚠️ Implementation appears complete; dedicated test pending**

---

# Phase 2.7 — Graceful Shutdown

## Current Implementation

`SocketServer::stop()` already performs shutdown work:

1. Marks server as not running
2. Shuts down listening socket
3. Closes listening socket
4. Joins the accept thread
5. Joins the heartbeat thread
6. Extracts connected clients
7. Stops each client
8. Clears the bound port

Current shutdown sequence:

```text
stop()
  │
  ├── running = false
  │
  ├── shutdown(server socket)
  │
  ├── close(server socket)
  │
  ├── join accept thread
  │
  ├── join heartbeat thread
  │
  ├── stop clients
  │
  └── boundPort = 0
```

## Remaining Verification

A dedicated shutdown test should verify:

* `stop()` terminates the server
* `isRunning()` becomes false
* listening socket is closed
* accept loop exits
* heartbeat loop exits
* connected clients are stopped
* client registry is cleared
* `port()` becomes `0`
* server can potentially be started again safely if supported

### Important Observation

The heartbeat thread currently sleeps for the configured heartbeat interval.

Therefore shutdown may wait for the heartbeat thread's current sleep interval before it exits.

For the default configuration:

```text
heartbeat interval = 10 seconds
```

This may make shutdown slower than necessary.

This should be measured before changing the implementation.

**Status: ⚠️ Needs dedicated verification**

---

# Phase 2.8 — Raw TCP / `nc` Verification

The roadmap requires useful manual transport verification.

Expected debugging workflow:

```bash
nc localhost <engine-port>
```

The connection should allow observation of transport behavior.

Because the protocol is currently:

```text
4-byte length prefix + JSON payload
```

plain `nc` may not display the payload cleanly without accounting for the binary framing header.

Therefore this requirement should be verified using an appropriate TCP debugging method rather than assuming plain terminal text output is sufficient.

**Status: ⏳ Pending verification**

---

# Documentation Consistency

## Known Issue

`docs/03-data-model.md` currently describes socket streams as:

```text
One event per line
```

However, the actual C++ transport implementation uses:

```text
4-byte big-endian length prefix
+
JSON payload
```

These two descriptions are inconsistent.

## Required Correction

The documentation should eventually describe the actual transport as:

```text
Length-prefixed JSON messages over TCP.
```

The implementation should **not** be rewritten merely to match the outdated documentation.

**Status: ⚠️ Documentation correction pending**

---

# Testing Status

## Current Test Suite

The C++ test suite currently reports:

```text
13/13 tests passed
100% tests passed
```

The existing transport coverage includes:

* Network server
* Client connection
* HELLO message
* Heartbeat
* Heartbeat timeout
* Broadcast
* Message serialization
* Frame extraction
* Partial frames
* Multiple frames
* Market pipeline
* Other order-book functionality

## Additional Tests Required

```text
[ ] Reconnection integration test
[ ] Graceful shutdown integration test
[ ] Optional server restart test
[ ] Raw transport/manual debugging verification
```

---

# Current Git State

Latest known state:

```text
Branch:
main

HEAD:
2c65ccf

Remote:
origin/main

Working tree:
clean
```

Latest relevant commits:

```text
2c65ccf Merge pull request #17 from adarsh0707-kumar/phase2.3-connection-handling
66d8de7 feat(engine): implement connection heartbeat handling
c44bc5f Merge pull request #16 from adarsh0707-kumar/phase2.1-cpp-transport
```

---

# Remaining Phase 2 Work

The immediate remaining work is intentionally small and focused.

## Step 1 — Reconnection Test

```text
⏳ Add test_client_reconnects()
```

Verify that a disconnected client can be replaced by a new connection.

---

## Step 2 — Graceful Shutdown Test

```text
⏳ Add shutdown lifecycle test
```

Verify that all server threads, sockets, and clients terminate correctly.

---

## Step 3 — Evaluate Shutdown Latency

Measure whether the heartbeat thread's sleep causes unacceptable shutdown delay.

Only change the implementation if testing demonstrates that the delay is a problem.

---

## Step 4 — Transport Documentation

Correct documentation that currently describes newline-delimited socket messages.

Document the actual:

```text
4-byte big-endian length-prefixed JSON protocol
```

---

## Step 5 — Phase 2 Exit Verification

Confirm all roadmap requirements:

```text
[ ] Server
[ ] Connection handling
[ ] Framing
[ ] Serialization
[ ] Reconnection behavior
[ ] Graceful shutdown
[ ] Useful logging
[ ] Tests
[ ] Manual transport verification
[ ] Documentation consistency
```

When all are complete:

```text
Phase 2 — C++ Transport
Status: ✅ COMPLETE
```

---

# Upcoming Roadmap

After Phase 2 is formally completed, development proceeds to:

## Phase 3 — Python Analytics

Planned components:

```text
VWAP
SMA
EMA
Position
PnL
Drawdown
```

Then:

```text
Phase 4 — Node Gateway
Phase 5 — React Dashboard
Phase 6 — Docker
Phase 7 — Testing & Hardening
Phase 8 — Observability
Phase 9 — Performance Mode
Phase 10 — Portfolio Release
```

---

# Development Rule

Before implementing a new component:

1. Check the roadmap.
2. Check this changelog.
3. Inspect the existing implementation.
4. Do not duplicate functionality that already exists.
5. Add focused tests for missing behavior.
6. Run the relevant tests.
7. Run the full test suite.
8. Update this changelog.
9. Commit using a focused conventional commit.
10. Merge only after verification.

This changelog should remain a factual record of what has actually been implemented and verified, rather than a list of assumptions.
