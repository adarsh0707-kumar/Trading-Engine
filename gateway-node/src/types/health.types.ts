export interface HealthResponse {
  readonly status: "ok";
  readonly service: "gateway";
}

export interface ReadinessResponse {
  readonly status: "ready" | "not_ready";
  readonly service: "gateway";
  readonly dependencies: {
    readonly gateway: "ok";
    readonly engine: "connected" | "disconnected";
    readonly analytics: "connected" | "disconnected";
  };
}
