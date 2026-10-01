import type { GatewayStatus, StatusProvider } from "./status.types.ts";

export function createStatusProvider(): StatusProvider {
  return {
    getStatus(): GatewayStatus {
      return {
        gateway: "ok",
        engine: "disconnected",
        analytics: "disconnected",
      };
    },
  };
}
