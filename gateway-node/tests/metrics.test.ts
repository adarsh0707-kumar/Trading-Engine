import { describe, expect, test } from "bun:test";

import { createGatewayMetrics } from "../src/metrics/metrics.ts";

describe("gateway metrics", () => {
  test("records engine, analytics, websocket and rate-limit metrics", async () => {
    const metrics = createGatewayMetrics();
    const now = Date.now();

    metrics.recordEngineState("connected");
    metrics.recordEngineMessage();
    metrics.recordEngineHeartbeat();
    metrics.recordEngineTrade();
    metrics.recordEngineReconnectAttempt();
    metrics.recordEngineConnectionFailure();
    metrics.recordEngineProtocolFailure();
    metrics.recordEngineTimeoutFailure();
    metrics.recordEngineLivenessFailure();
    metrics.setEngineLastMessageAt(now);
    metrics.setEngineLastHeartbeatAt(now);

    metrics.recordAnalyticsState("connected");
    metrics.recordAnalyticsUpdate();
    metrics.recordAnalyticsRiskEvent();
    metrics.recordAnalyticsError();
    metrics.recordAnalyticsTradeSent();
    metrics.recordAnalyticsTradeSendFailure();
    metrics.recordAnalyticsQueueOverflow();

    metrics.recordWebSocketConnection();
    metrics.recordWebSocketDisconnection();
    metrics.recordWebSocketSubscriptionUpdate();
    metrics.recordWebSocketQueueOverflow();
    metrics.recordWebSocketHeartbeatTimeout();
    metrics.recordWebSocketPublishedEvent("TRADE");
    metrics.setWebSocketClients(2);

    metrics.recordHttpRequest("GET", 200);
    metrics.observeHttpRequestDuration("GET", 0.025);
    metrics.recordRateLimitRejection();

    const output = await metrics.getMetrics();

    expect(output).toContain("gateway_http_requests_total{method="GET",status_code="200"} 1");
    expect(output).toContain("gateway_http_request_duration_seconds");
    expect(output).toContain("gateway_engine_connected 1");
    expect(output).toContain("gateway_engine_messages_total 1");
    expect(output).toContain("gateway_engine_heartbeats_total 1");
    expect(output).toContain("gateway_engine_trade_events_total 1");
    expect(output).toContain("gateway_engine_reconnect_attempts_total 1");
    expect(output).toContain("gateway_engine_connection_failures_total 1");
    expect(output).toContain("gateway_engine_protocol_failures_total 1");
    expect(output).toContain("gateway_engine_timeout_failures_total 1");
    expect(output).toContain("gateway_engine_liveness_failures_total 1");
    expect(output).toContain("gateway_engine_last_message_timestamp_seconds");
    expect(output).toContain("gateway_engine_last_heartbeat_timestamp_seconds");
    expect(output).toContain("gateway_analytics_connected 1");
    expect(output).toContain("gateway_analytics_updates_total 1");
    expect(output).toContain("gateway_analytics_risk_events_total 1");
    expect(output).toContain("gateway_analytics_errors_total 1");
    expect(output).toContain("gateway_analytics_trades_sent_total 1");
    expect(output).toContain("gateway_analytics_trade_send_failures_total 1");
    expect(output).toContain("gateway_analytics_queue_overflows_total 1");
    expect(output).toContain("gateway_websocket_connected_clients 2");
    expect(output).toContain("gateway_websocket_connections_total 1");
    expect(output).toContain("gateway_websocket_disconnections_total 1");
    expect(output).toContain("gateway_websocket_subscription_updates_total 1");
    expect(output).toContain("gateway_websocket_queue_overflows_total 1");
    expect(output).toContain("gateway_websocket_heartbeat_timeouts_total 1");
    expect(output).toContain("gateway_websocket_published_events_total{event_type="TRADE"} 1");
    expect(output).toContain("gateway_rate_limit_rejections_total 1");
  });

  test("keeps connection gauges disconnected by default", async () => {
    const metrics = createGatewayMetrics();
    const output = await metrics.getMetrics();

    expect(output).toContain("gateway_engine_connected 0");
    expect(output).toContain("gateway_analytics_connected 0");
    expect(output).toContain("gateway_websocket_connected_clients 0");
  });
});
