# Resilience Error Model

## Purpose

Phase 4.7 establishes explicit failure boundaries for the Gateway and analytics
integration. This document defines failure categories and their default
handling before runtime resilience behavior is expanded in later 4.7.x phases.

## Failure categories

| Category | Meaning | Recoverable | Boundary action |
| --- | --- | --- | --- |
| Connection failure | TCP connect, socket, or peer disconnect failure | Yes | Mark dependency disconnected; reconnect according to client policy |
| Timeout failure | Connection or request exceeded its configured deadline | Yes | Abort the timed operation; reconnect/retry where configured |
| Protocol failure | Invalid frame, unsupported message shape, invalid UTF-8/JSON, or protocol version violation | Usually no for the current connection | Close the affected connection; do not process the invalid message |
| Validation failure | Structurally valid transport data violates domain/contract validation | No for the invalid message | Reject the message; preserve service/process availability |
| Queue overflow | Bounded outbound queue has reached its configured capacity | Yes at system level | Reject/drop the new message; report the saturation event |
| Dependency unavailable | Required downstream service is disconnected or has no usable data | Yes | Degrade the dependent feature; do not crash the gateway |
| Processing failure | Analytics callback/pipeline processing fails after transport acceptance | Message-dependent | Isolate the failing message/callback; log the failure and keep the transport alive when safe |
| Shutdown/cancellation | Intentional lifecycle stop | No reconnect | Close resources and terminate the active lifecycle cleanly |

## Failure boundaries

### Engine TCP boundary

The Gateway engine client owns TCP lifecycle and framing. Socket failures,
connection timeouts, and peer closes are transport failures and trigger the
existing reconnect lifecycle while the client is running.

Malformed engine protocol data is a protocol failure. The active connection is
closed so that a potentially desynchronized stream is not reused.

### Analytics TCP boundary

The Gateway analytics client and Python Gateway receiver own the analytics TCP
transport. Connection loss is recoverable. Invalid frames or invalid analytics
messages are isolated to the active connection/message according to the
transport side that detected the failure.

### Analytics processing boundary

Once a complete analytics message has passed transport framing, contract/domain
validation remains separate from transport handling. A processing or callback
failure must not be allowed to terminate the receiver's lifecycle accidentally.

### Queue boundary

The Gateway analytics outbound queue is intentionally bounded. Reaching the
limit is not a reason to grow memory without bound. The producer reports the
overflow and the new message is rejected according to the queue policy.

## Logging and observability

Failures should be observable with:

- failure category
- dependency/boundary
- event/request identifier when available
- retry/reconnect attempt when applicable
- queue size/capacity when applicable
- underlying error message

Connection lifecycle should use normal lifecycle logs. Expected disconnects
during shutdown should not be reported as unexpected failures.

## Recovery rules

1. Do not retry protocol-invalid payloads unchanged.
2. Do not reconnect after intentional shutdown.
3. Do not let a dependency failure crash unrelated Gateway HTTP/WebSocket work.
4. Keep bounded queues bounded.
5. Preserve identifiers when reporting failures.
6. Prefer failing one message/connection over terminating the process.
7. Later 4.7.x phases may refine these policies, but must remain compatible
   with this taxonomy unless the model is explicitly revised.

## Phase mapping

- **4.7.1** — taxonomy and failure boundaries
- **4.7.2** — engine connection resilience
- **4.7.3** — analytics connection resilience
- **4.7.4** — queue/backpressure behavior
- **4.7.5** — timeout/retry/recovery policies
- **4.7.6** — failure isolation and graceful degradation
- **4.7.7** — resilience test matrix
- **4.7.8** — observability and final documentation
