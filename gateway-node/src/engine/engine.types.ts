export type EngineAction = "start" | "stop" | "reset";

export interface EngineActionResult {
  readonly action: EngineAction;
  readonly status: "accepted";
}

export interface EngineProvider {
  start(): EngineActionResult | null;
  stop(): EngineActionResult | null;
  reset(): EngineActionResult | null;
}
