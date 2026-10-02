import type { StatusProvider, GatewayStatus } from "./status.types.ts";

export interface StatusProviderOptions {
  readonly isEngineConnected?: () => boolean;
  readonly isAnalyticsConnected?: () => boolean;
}

export function createStatusProvider(
  options: StatusProviderOptions = {},
): StatusProvider {
  return {
    getStatus(): GatewayStatus {
      return {
        gateway: "ok",
        engine: options.isEngineConnected?.() ? "connected" : "disconnected",
        analytics: options.isAnalyticsConnected?.()
          ? "connected"
          : "disconnected",
      };
    },
  };
}
