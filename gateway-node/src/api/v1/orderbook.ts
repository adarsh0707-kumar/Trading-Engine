import type { FastifyInstance } from "fastify";

import { dependencyUnavailable } from "../../errors/api-error.ts";
import type { OrderBookProvider } from "../../orderbook/orderbook.types.ts";
import {
  apiErrorSchema,
  orderBookResponseSchema,
} from "./schemas.ts";

export interface OrderBookRouteOptions {
  readonly orderBookProvider: OrderBookProvider;
}

export async function registerOrderBookRoute(
  app: FastifyInstance,
  options: OrderBookRouteOptions,
): Promise<void> {
  app.get("/api/v1/orderbook", {
    schema: {
      response: {
        200: orderBookResponseSchema,
        404: apiErrorSchema,
        503: apiErrorSchema,
        500: apiErrorSchema,
      },
    },
  }, async () => {
    const orderBook = await options.orderBookProvider.getOrderBook();

    if (orderBook === null) {
      throw dependencyUnavailable("Order book state is unavailable");
    }

    return {
      data: orderBook,
    };
  });
}
