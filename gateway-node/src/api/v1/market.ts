import type { FastifyInstance } from "fastify";

import { dependencyUnavailable } from "../../errors/api-error.ts";
import type { MarketProvider } from "../../market/market.types.ts";
import {
  apiErrorSchema,
  marketResponseSchema,
} from "./schemas.ts";

export interface MarketRouteOptions {
  readonly marketProvider: MarketProvider;
}

export async function registerMarketRoute(
  app: FastifyInstance,
  options: MarketRouteOptions,
): Promise<void> {
  app.get("/api/v1/market", {
    schema: {
      response: {
        200: marketResponseSchema,
        404: apiErrorSchema,
        503: apiErrorSchema,
        500: apiErrorSchema,
      },
    },
  }, async () => {
    const market = options.marketProvider.getMarket();

    if (market === null) {
      throw dependencyUnavailable("Market state is unavailable");
    }

    return {
      data: market,
    };
  });
}
