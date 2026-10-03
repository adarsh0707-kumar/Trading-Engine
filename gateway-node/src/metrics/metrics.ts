import client from "prom-client";

const registry = new client.Registry();

client.collectDefaultMetrics({
  register: registry,
});

export type EngineMetricState =
  | "connecting"
  | "connected"
  | "disconnected";

export interface GatewayMetrics {
  readonly registry: client.Registry;
  readonly contentType: string;
  readonly getMetrics: () => Promise<string>;
  readonly recordEngineState: (state: EngineMetricState) => void;
  readonly recordEngineMessage: () => void;
  readonly recordEngineHeartbeat: () => void;
  readonly recordEngineReconnectAttempt: () => void;
  readonly recordEngineConnectionFailure: () => void;
  readonly recordEngineProtocolFailure: () => void;
  readonly recordEngineTimeoutFailure: () => void;
  readonly setEngineLastMessageAt: (timestampMs: number) => void;
  readonly setEngineLastHeartbeatAt: (timestampMs: number) => void;
}

export function createGatewayMetrics(): GatewayMetrics {
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

  const engineMessages = new client.Counter({
    name: "gateway_engine_messages_total",
    help: "Total engine messages received by the gateway.",
    registers: [registry],
  });

  const engineHeartbeats = new client.Counter({
    name: "gateway_engine_heartbeats_total",
    help: "Total engine heartbeat messages received by the gateway.",
    registers: [registry],
  });

  const engineReconnectAttempts = new client.Counter({
    name: "gateway_engine_reconnect_attempts_total",
    help: "Total engine reconnect attempts scheduled by the gateway.",
    registers: [registry],
  });

  const engineConnectionFailures = new client.Counter({
    name: "gateway_engine_connection_failures_total",
    help: "Total engine connection failures observed by the gateway.",
    registers: [registry],
  });

  const engineProtocolFailures = new client.Counter({
    name: "gateway_engine_protocol_failures_total",
    help: "Total engine protocol failures observed by the gateway.",
    registers: [registry],
  });

  const engineTimeoutFailures = new client.Counter({
    name: "gateway_engine_timeout_failures_total",
    help: "Total engine connection timeout failures observed by the gateway.",
    registers: [registry],
  });

  return {
    registry,
    contentType: registry.contentType,
    getMetrics: () => registry.metrics(),
    recordEngineState: (state) => {
      engineConnected.set(state === "connected" ? 1 : 0);
    },
    recordEngineMessage: () => {
      engineMessages.inc();
    },
    recordEngineHeartbeat: () => {
      engineHeartbeats.inc();
    },
    recordEngineReconnectAttempt: () => {
      engineReconnectAttempts.inc();
    },
    recordEngineConnectionFailure: () => {
      engineConnectionFailures.inc();
    },
    recordEngineProtocolFailure: () => {
      engineProtocolFailures.inc();
    },
    recordEngineTimeoutFailure: () => {
      engineTimeoutFailures.inc();
    },
    setEngineLastMessageAt: (timestampMs) => {
      engineLastMessageTimestamp.set(timestampMs / 1000);
    },
    setEngineLastHeartbeatAt: (timestampMs) => {
      engineLastHeartbeatTimestamp.set(timestampMs / 1000);
    },
  };
}
