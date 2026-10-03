import { describe, expect, test } from "bun:test";

import { createGatewayMetrics } from "../src/metrics/metrics.ts";

describe("gateway engine metrics", () => {
  test("records engine state, liveness, reconnects and failures", async () => {
    const metrics = createGatewayMetrics();
    const now = Date.now();

    metrics.recordEngineState("connected");
    metrics.recordEngineMessage();
    metrics.recordEngineHeartbeat();
    metrics.recordEngineReconnectAttempt();
    metrics.recordEngineConnectionFailure();
    metrics.recordEngineProtocolFailure();
    metrics.recordEngineTimeoutFailure();
    metrics.setEngineLastMessageAt(now);
    metrics.setEngineLastHeartbeatAt(now);

    const output = await metrics.getMetrics();

    expect(output).toContain("gateway_engine_connected 1");
    expect(output).toContain("gateway_engine_messages_total 1");
    expect(output).toContain("gateway_engine_heartbeats_total 1");
    expect(output).toContain("gateway_engine_reconnect_attempts_total 1");
    expect(output).toContain("gateway_engine_connection_failures_total 1");
    expect(output).toContain("gateway_engine_protocol_failures_total 1");
    expect(output).toContain("gateway_engine_timeout_failures_total 1");
    expect(output).toContain("gateway_engine_last_message_timestamp_seconds");
    expect(output).toContain("gateway_engine_last_heartbeat_timestamp_seconds");
  });
});
