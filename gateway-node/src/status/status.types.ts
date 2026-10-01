export type DependencyStatus = "connected" | "disconnected";

export interface GatewayStatus {
  readonly gateway: "ok";
  readonly engine: DependencyStatus;
  readonly analytics: DependencyStatus;
}

export interface StatusProvider {
  getStatus(): GatewayStatus;
}
