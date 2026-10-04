export interface GatewayStatus {
  gateway: "ok" | "error" | string;
  engine: "connected" | "disconnected" | string;
  analytics: "connected" | "disconnected" | string;
}

export interface EngineStatus {
  state: string;
  connectedAt: string | null;
  lastMessageAt: string | null;
  lastHeartbeatAt: string | null;
  reconnectAttempts: number;
}
