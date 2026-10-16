import type { FastifyInstance } from "fastify";

import { dataNotReady, dependencyUnavailable } from "../../errors/api-error.ts";
import type { AnalyticsProvider } from "../../analytics/analytics.types.ts";
import {
  analyticsResponseSchema,
  apiErrorSchema,
} from "./schemas.ts";

export interface AnalyticsRouteOptions {
  readonly analyticsProvider: AnalyticsProvider;
  readonly isAnalyticsConnected: () => boolean;
}

export async function registerAnalyticsRoute(
  app: FastifyInstance,
  options: AnalyticsRouteOptions,
): Promise<void> {
  app.get("/api/v1/analytics", {
    schema: {
      response: {
        200: analyticsResponseSchema,
        404: apiErrorSchema,
        503: apiErrorSchema,
        500: apiErrorSchema,
      },
    },
  }, async () => {
    const analytics = options.analyticsProvider.getAnalytics();

    if (analytics === null) {
      if (options.isAnalyticsConnected()) {
        throw dataNotReady("Analytics snapshot has not been published yet");
      }
      throw dependencyUnavailable("Analytics service is unavailable");
    }

    return {
      data: analytics,
    };
  });
}
