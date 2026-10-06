export interface GatewayStatus {
  gateway: "ok" | "error" | string;
  engine: "connected" | "disconnected" | string;
  analytics: "connected" | "disconnected" | string;
}

export interface EngineStatus {
  state: string;
  connectedAt: number | null;
  lastMessageAt: number | null;
  lastHeartbeatAt: number | null;
  reconnectAttempts: number;
}

export type SystemConnectionState = "healthy" | "degraded" | "offline";
