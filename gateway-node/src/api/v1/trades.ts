import type { FastifyInstance } from "fastify";

import { dependencyUnavailable } from "../../errors/api-error.ts";
import type { TradesProvider } from "../../trades/trades.types.ts";
import {
  apiErrorSchema,
  tradesResponseSchema,
} from "./schemas.ts";

export interface TradesRouteOptions {
  readonly tradesProvider: TradesProvider;
}

export async function registerTradesRoute(
  app: FastifyInstance,
  options: TradesRouteOptions,
): Promise<void> {
  app.get("/api/v1/trades", {
    schema: {
      response: {
        200: tradesResponseSchema,
        404: apiErrorSchema,
        503: apiErrorSchema,
        500: apiErrorSchema,
      },
    },
  }, async () => {
    const trades = options.tradesProvider.getTrades();

    if (trades === null) {
      throw dependencyUnavailable("Trade history is unavailable");
    }

    return {
      data: trades,
    };
  });
}
