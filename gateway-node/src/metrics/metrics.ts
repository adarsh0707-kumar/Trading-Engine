import client from "prom-client";

export type EngineMetricState =
  | "connecting"
  | "connected"
  | "disconnected";

export type AnalyticsMetricState = EngineMetricState;

export interface GatewayMetrics {
  readonly registry: client.Registry;
  readonly contentType: string;
  readonly getMetrics: () => Promise<string>;

  readonly recordHttpRequest: (method: string, statusCode: number) => void;
  readonly observeHttpRequestDuration: (method: string, durationSeconds: number) => void;

  readonly recordEngineState: (state: EngineMetricState) => void;
  readonly recordEngineMessage: () => void;
  readonly recordEngineHeartbeat: () => void;
  readonly recordEngineTrade: () => void;
  readonly recordEngineReconnectAttempt: () => void;
  readonly recordEngineConnectionFailure: () => void;
  readonly recordEngineProtocolFailure: () => void;
  readonly recordEngineTimeoutFailure: () => void;
  readonly recordEngineLivenessFailure: () => void;
  readonly setEngineLastMessageAt: (timestampMs: number) => void;
  readonly setEngineLastHeartbeatAt: (timestampMs: number) => void;

  readonly recordAnalyticsState: (state: AnalyticsMetricState) => void;
  readonly recordAnalyticsUpdate: () => void;
  readonly recordAnalyticsRiskEvent: () => void;
  readonly recordAnalyticsError: () => void;
  readonly recordAnalyticsTradeSent: () => void;
  readonly recordAnalyticsTradeSendFailure: () => void;
  readonly recordAnalyticsQueueOverflow: () => void;

  readonly recordWebSocketConnection: () => void;
  readonly recordWebSocketDisconnection: () => void;
  readonly recordWebSocketSubscriptionUpdate: () => void;
  readonly recordWebSocketQueueOverflow: () => void;
  readonly recordWebSocketHeartbeatTimeout: () => void;
  readonly recordWebSocketPublishedEvent: (eventType: string) => void;
  readonly setWebSocketClients: (count: number) => void;

  readonly recordRateLimitRejection: () => void;
  readonly setGatewayReadiness: (ready: boolean) => void;
}

function createCounter(
  registry: client.Registry,
  name: string,
  help: string,
  labelNames: readonly string[] = [],
): client.Counter<string> {
  return new client.Counter({
    name,
    help,
    labelNames,
    registers: [registry],
  });
}

export function createGatewayMetrics(): GatewayMetrics {
  const registry = new client.Registry();

  client.collectDefaultMetrics({
    register: registry,
  });

  const httpRequests = createCounter(
    registry,
    "gateway_http_requests_total",
    "Total HTTP requests completed by the gateway.",
    ["method", "status_code"],
  );

  const httpRequestDuration = new client.Histogram({
    name: "gateway_http_request_duration_seconds",
    help: "HTTP request duration observed by the gateway in seconds.",
    labelNames: ["method"],
    buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5],
    registers: [registry],
  });

  const engineConnected = new client.Gauge({
    name: "gateway_engine_connected",
    help: "Whether the gateway engine connection is currently established.",
    registers: [registry],
  });

  const engineLastMessageTimestamp = new client.Gauge({
    name: "gateway_engine_last_message_timestamp_seconds",
    help: "Unix timestamp of the last engine message received by the gateway.",
    registers: [registry],
  });

  const engineLastHeartbeatTimestamp = new client.Gauge({
    name: "gateway_engine_last_heartbeat_timestamp_seconds",
    help: "Unix timestamp of the last engine heartbeat received by the gateway.",
    registers: [registry],
  });

  const engineMessages = createCounter(
    registry,
    "gateway_engine_messages_total",
    "Total engine messages received by the gateway.",
  );

  const engineHeartbeats = createCounter(
    registry,
    "gateway_engine_heartbeats_total",
    "Total engine heartbeat messages received by the gateway.",
  );

  const engineTrades = createCounter(
    registry,
    "gateway_engine_trade_events_total",
    "Total normalized engine trade events received by the gateway.",
  );

  const engineReconnectAttempts = createCounter(
    registry,
    "gateway_engine_reconnect_attempts_total",
    "Total engine reconnect attempts scheduled by the gateway.",
  );

  const engineConnectionFailures = createCounter(
    registry,
    "gateway_engine_connection_failures_total",
    "Total engine connection failures observed by the gateway.",
  );

  const engineProtocolFailures = createCounter(
    registry,
    "gateway_engine_protocol_failures_total",
    "Total engine protocol failures observed by the gateway.",
  );

  const engineTimeoutFailures = createCounter(
    registry,
    "gateway_engine_timeout_failures_total",
    "Total engine connection timeout failures observed by the gateway.",
  );

  const engineLivenessFailures = createCounter(
    registry,
    "gateway_engine_liveness_failures_total",
    "Total engine heartbeat liveness failures observed by the gateway.",
  );

  const analyticsConnected = new client.Gauge({
    name: "gateway_analytics_connected",
    help: "Whether the gateway analytics connection is currently established.",
    registers: [registry],
  });

  const analyticsUpdates = createCounter(
    registry,
    "gateway_analytics_updates_total",
    "Total analytics update messages received by the gateway.",
  );

  const analyticsRiskEvents = createCounter(
    registry,
    "gateway_analytics_risk_events_total",
    "Total analytics risk event messages received by the gateway.",
  );

  const analyticsErrors = createCounter(
    registry,
    "gateway_analytics_errors_total",
    "Total analytics client errors observed by the gateway.",
  );

  const analyticsTradesSent = createCounter(
    registry,
    "gateway_analytics_trades_sent_total",
    "Total engine trade events accepted for analytics delivery.",
  );

  const analyticsTradeSendFailures = createCounter(
    registry,
    "gateway_analytics_trade_send_failures_total",
    "Total engine trade events rejected by the analytics client.",
  );

  const analyticsQueueOverflows = createCounter(
    registry,
    "gateway_analytics_queue_overflows_total",
    "Total analytics outbound queue overflow failures observed by the gateway.",
  );

  const websocketConnectedClients = new client.Gauge({
    name: "gateway_websocket_connected_clients",
    help: "Current number of connected WebSocket clients.",
    registers: [registry],
  });

  const websocketConnections = createCounter(
    registry,
    "gateway_websocket_connections_total",
    "Total WebSocket client connections accepted by the gateway.",
  );

  const websocketDisconnections = createCounter(
    registry,
    "gateway_websocket_disconnections_total",
    "Total WebSocket client disconnections observed by the gateway.",
  );

  const websocketSubscriptionUpdates = createCounter(
    registry,
    "gateway_websocket_subscription_updates_total",
    "Total WebSocket subscription update messages accepted by the gateway.",
  );

  const websocketQueueOverflows = createCounter(
    registry,
    "gateway_websocket_queue_overflows_total",
    "Total WebSocket client queue overflow events observed by the gateway.",
  );

  const websocketHeartbeatTimeouts = createCounter(
    registry,
    "gateway_websocket_heartbeat_timeouts_total",
    "Total WebSocket client heartbeat timeouts observed by the gateway.",
  );

  const websocketPublishedEvents = createCounter(
    registry,
    "gateway_websocket_published_events_total",
    "Total gateway events published to the WebSocket hub.",
    ["event_type"],
  );

  const gatewayReady = new client.Gauge({
    name: "gateway_ready",
    help: "Whether the gateway is currently ready to serve traffic.",
    registers: [registry],
  });

  const rateLimitRejections = createCounter(
    registry,
    "gateway_rate_limit_rejections_total",
    "Total HTTP requests rejected by the gateway rate limit.",
  );

  return {
    registry,
    contentType: registry.contentType,
    getMetrics: () => registry.metrics(),

    recordHttpRequest: (method, statusCode) => {
      httpRequests.inc({ method, status_code: String(statusCode) });
    },
    observeHttpRequestDuration: (method, durationSeconds) => {
      httpRequestDuration.observe({ method }, durationSeconds);
    },

    recordEngineState: (state) => {
      engineConnected.set(state === "connected" ? 1 : 0);
    },
    recordEngineMessage: () => engineMessages.inc(),
    recordEngineHeartbeat: () => engineHeartbeats.inc(),
    recordEngineTrade: () => engineTrades.inc(),
    recordEngineReconnectAttempt: () => engineReconnectAttempts.inc(),
    recordEngineConnectionFailure: () => engineConnectionFailures.inc(),
    recordEngineProtocolFailure: () => engineProtocolFailures.inc(),
    recordEngineTimeoutFailure: () => engineTimeoutFailures.inc(),
    recordEngineLivenessFailure: () => engineLivenessFailures.inc(),
    setEngineLastMessageAt: (timestampMs) => {
      engineLastMessageTimestamp.set(timestampMs / 1000);
    },
    setEngineLastHeartbeatAt: (timestampMs) => {
      engineLastHeartbeatTimestamp.set(timestampMs / 1000);
    },

    recordAnalyticsState: (state) => {
      analyticsConnected.set(state === "connected" ? 1 : 0);
    },
    recordAnalyticsUpdate: () => analyticsUpdates.inc(),
    recordAnalyticsRiskEvent: () => analyticsRiskEvents.inc(),
    recordAnalyticsError: () => analyticsErrors.inc(),
    recordAnalyticsTradeSent: () => analyticsTradesSent.inc(),
    recordAnalyticsTradeSendFailure: () => analyticsTradeSendFailures.inc(),
    recordAnalyticsQueueOverflow: () => analyticsQueueOverflows.inc(),

    recordWebSocketConnection: () => websocketConnections.inc(),
    recordWebSocketDisconnection: () => websocketDisconnections.inc(),
    recordWebSocketSubscriptionUpdate: () => websocketSubscriptionUpdates.inc(),
    recordWebSocketQueueOverflow: () => websocketQueueOverflows.inc(),
    recordWebSocketHeartbeatTimeout: () => websocketHeartbeatTimeouts.inc(),
    recordWebSocketPublishedEvent: (eventType) => {
      websocketPublishedEvents.inc({ event_type: eventType });
    },
    setWebSocketClients: (count) => websocketConnectedClients.set(count),

    recordRateLimitRejection: () => rateLimitRejections.inc(),
    setGatewayReadiness: (ready) => gatewayReady.set(ready ? 1 : 0),
  };
}
