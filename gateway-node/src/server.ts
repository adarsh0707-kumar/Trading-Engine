import cors from "@fastify/cors";
import Fastify, { type FastifyInstance } from "fastify";

import { registerHealthRoutes } from "./api/health.ts";
import { registerV1Routes } from "./api/v1/index.ts";
import { loadConfig, type GatewayConfig } from "./config/config.ts";
import { createGatewayMetrics } from "./metrics/metrics.ts";
import { registerErrorHandler } from "./errors/error-handler.ts";
import type { EngineProvider } from "./engine/engine.types.ts";
import { createStatusProvider } from "./status/status.provider.ts";
import type { StatusProvider } from "./status/status.types.ts";
import type { AnalyticsProvider } from "./analytics/analytics.types.ts";
import type { MarketProvider } from "./market/market.types.ts";
import type { OrderBookProvider } from "./orderbook/orderbook.types.ts";
import type { TradesProvider } from "./trades/trades.types.ts";

export interface GatewayServer {
  readonly app: FastifyInstance;
  readonly config: GatewayConfig;
  readonly start: () => Promise<void>;
  readonly stop: () => Promise<void>;
}

export interface GatewayServerOptions {
  readonly statusProvider?: StatusProvider;
  readonly marketProvider?: MarketProvider;
  readonly orderBookProvider?: OrderBookProvider;
  readonly tradesProvider?: TradesProvider;
  readonly analyticsProvider?: AnalyticsProvider;
  readonly engineProvider?: EngineProvider;
}

export function createGatewayServer(
  environment: Record<string, string | undefined> = process.env,
  options: GatewayServerOptions = {},
): GatewayServer {
  const config = loadConfig(environment);

  const app = Fastify({
    logger: {
      level: config.logging.level,
    },
    bodyLimit: config.http.bodyLimitBytes,
    connectionTimeout: config.http.requestTimeoutMs,
  });

  registerErrorHandler(app);

  app.register(cors, {
    origin: config.cors.origin,
  });

  app.register(registerHealthRoutes);

  const statusProvider = options.statusProvider ?? createStatusProvider();

  app.register(registerV1Routes, {
    statusProvider,
    marketProvider: options.marketProvider,
    orderBookProvider: options.orderBookProvider,
    tradesProvider: options.tradesProvider,
    analyticsProvider: options.analyticsProvider,
    engineProvider: options.engineProvider,
  });

  if (config.metrics.enabled) {
    const metrics = createGatewayMetrics();

    app.get(config.metrics.path, async (_request, reply) => {
      reply.header("Content-Type", metrics.contentType);

      return metrics.getMetrics();
    });
  }

  let started = false;

  const start = async (): Promise<void> => {
    if (started) {
      return;
    }

    await app.listen({
      host: config.gateway.host,
      port: config.gateway.port,
    });

    started = true;
  };

  const stop = async (): Promise<void> => {
    if (!started) {
      return;
    }

    await app.close();
    started = false;
  };

  return {
    app,
    config,
    start,
    stop,
  };
}

export async function startGateway(): Promise<void> {
  const gateway = createGatewayServer();

  const shutdown = async (signal: string): Promise<void> => {
    gateway.app.log.info({ signal }, "gateway_shutdown_started");

    try {
      await gateway.stop();
      gateway.app.log.info("gateway_shutdown_completed");
      process.exit(0);
    } catch (error) {
      gateway.app.log.error({ error }, "gateway_shutdown_failed");
      process.exit(1);
    }
  };

  process.once("SIGINT", () => {
    void shutdown("SIGINT");
  });

  process.once("SIGTERM", () => {
    void shutdown("SIGTERM");
  });

  try {
    await gateway.start();

    gateway.app.log.info(
      {
        host: gateway.config.gateway.host,
        port: gateway.config.gateway.port,
      },
      "gateway_started",
    );
  } catch (error) {
    gateway.app.log.error({ error }, "gateway_start_failed");
    process.exit(1);
  }
}

if (import.meta.main) {
  await startGateway();
}
