import type { FastifyInstance } from "fastify";

import { createEngineProvider } from "../../engine/engine.provider.ts";
import type { EngineProvider } from "../../engine/engine.types.ts";
import { createAnalyticsProvider } from "../../analytics/analytics.provider.ts";
import type { AnalyticsProvider } from "../../analytics/analytics.types.ts";
import { createMarketProvider } from "../../market/market.provider.ts";
import type { MarketProvider } from "../../market/market.types.ts";
import { createOrderBookProvider } from "../../orderbook/orderbook.provider.ts";
import type { OrderBookProvider } from "../../orderbook/orderbook.types.ts";
import { createStatusProvider } from "../../status/status.provider.ts";
import type { StatusProvider } from "../../status/status.types.ts";
import { createTradesProvider } from "../../trades/trades.provider.ts";
import type { TradesProvider } from "../../trades/trades.types.ts";
import { registerAnalyticsRoute } from "./analytics.ts";
import { registerEngineRoutes } from "./engine.ts";
import { registerMarketRoute } from "./market.ts";
import { registerOrderBookRoute } from "./orderbook.ts";
import { registerStatusRoute } from "./status.ts";
import { registerTradesRoute } from "./trades.ts";

export interface V1RouteOptions {
  readonly statusProvider?: StatusProvider;
  readonly marketProvider?: MarketProvider;
  readonly orderBookProvider?: OrderBookProvider;
  readonly tradesProvider?: TradesProvider;
  readonly analyticsProvider?: AnalyticsProvider;
  readonly engineProvider?: EngineProvider;
}

export async function registerV1Routes(
  app: FastifyInstance,
  options: V1RouteOptions = {},
): Promise<void> {
  const statusProvider = options.statusProvider ?? createStatusProvider();
  const marketProvider = options.marketProvider ?? createMarketProvider();
  const orderBookProvider =
    options.orderBookProvider ?? createOrderBookProvider();
  const tradesProvider = options.tradesProvider ?? createTradesProvider();
  const analyticsProvider =
    options.analyticsProvider ?? createAnalyticsProvider();
  const engineProvider = options.engineProvider ?? createEngineProvider();

  await registerStatusRoute(app, statusProvider);
  await registerAnalyticsRoute(app, {
    analyticsProvider,
  });
  await registerEngineRoutes(app, {
    engineProvider,
  });
  await registerMarketRoute(app, {
    marketProvider,
  });
  await registerOrderBookRoute(app, {
    orderBookProvider,
  });
  await registerTradesRoute(app, {
    tradesProvider,
  });
}
