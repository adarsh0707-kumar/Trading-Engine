import type {
  AnalyticsProvider,
  AnalyticsSnapshot,
} from "./analytics.types.ts";

export function createAnalyticsProvider(): AnalyticsProvider {
  return {
    getAnalytics(): AnalyticsSnapshot | null {
      return null;
    },
  };
}
