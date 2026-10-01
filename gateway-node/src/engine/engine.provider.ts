import type { EngineActionResult, EngineProvider } from "./engine.types.ts";

export function createEngineProvider(): EngineProvider {
  return {
    start(): EngineActionResult | null {
      return null;
    },

    stop(): EngineActionResult | null {
      return null;
    },

    reset(): EngineActionResult | null {
      return null;
    },
  };
}
