import type { FastifyInstance } from "fastify";

import { dependencyUnavailable } from "../../errors/api-error.ts";
import type { AnalyticsProvider } from "../../analytics/analytics.types.ts";
import {
  analyticsResponseSchema,
  apiErrorSchema,
} from "./schemas.ts";

export interface AnalyticsRouteOptions {
  readonly analyticsProvider: AnalyticsProvider;
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
      throw dependencyUnavailable("Analytics data is unavailable");
    }

    return {
      data: analytics,
    };
  });
}
