import cors from "@fastify/cors";
import websocket from "@fastify/websocket";
import Fastify, { type FastifyInstance } from "fastify";

import { registerHealthRoutes } from "./api/health.ts";
import { registerV1Routes } from "./api/v1/index.ts";
import { loadConfig, type GatewayConfig } from "./config/config.ts";
import { createGatewayMetrics } from "./metrics/metrics.ts";
import { registerErrorHandler } from "./errors/error-handler.ts";
import { createEngineEventClient, type EngineEventClient } from "./engine/engine-event-client.ts";
import {
  createAnalyticsClient,
  type AnalyticsClient,
} from "./analytics/analytics-client.ts";
import {
  createAnalyticsProvider,
  type MutableAnalyticsProvider,
} from "./analytics/analytics.provider.ts";
import type { EngineProvider } from "./engine/engine.types.ts";
import { createStatusProvider } from "./status/status.provider.ts";
import type { StatusProvider } from "./status/status.types.ts";
import type { AnalyticsProvider } from "./analytics/analytics.types.ts";
import type { MarketProvider } from "./market/market.types.ts";
import type { OrderBookProvider } from "./orderbook/orderbook.types.ts";
import type { TradesProvider } from "./trades/trades.types.ts";
import { createWebSocketHub, type WebSocketHub } from "./websocket/websocket-hub.ts";

export interface GatewayServer {
  readonly app: FastifyInstance;
  readonly config: GatewayConfig;
  readonly start: () => Promise<void>;
  readonly stop: () => Promise<void>;
  readonly websocketHub: WebSocketHub;
  readonly engineEventClient: EngineEventClient;
  readonly analyticsClient: AnalyticsClient;
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

  const websocketHub = createWebSocketHub({
    maxQueueSize: config.websocket.maxQueueSize,
    heartbeatIntervalMs: config.websocket.heartbeatIntervalMs,
  });

  const analyticsProvider =
    options.analyticsProvider ?? createAnalyticsProvider();

  const mutableAnalyticsProvider =
    "updateAnalytics" in analyticsProvider &&
    "updateRiskEvent" in analyticsProvider
      ? (analyticsProvider as MutableAnalyticsProvider)
      : undefined;

  const analyticsClient = createAnalyticsClient({
    host: config.analytics.host,
    port: config.analytics.port,
    connectTimeoutMs: config.analytics.connectTimeoutMs,
    reconnectInitialDelayMs: config.analytics.reconnectInitialDelayMs,
    reconnectMaxDelayMs: config.analytics.reconnectMaxDelayMs,
    reconnectMaxAttempts: config.analytics.reconnectMaxAttempts,
    maxQueueSize: config.analytics.maxQueueSize,
    onAnalyticsUpdate: (message) => {
      mutableAnalyticsProvider?.updateAnalytics(message);

      websocketHub.publish({
        type: "ANALYTICS_UPDATE",
        eventId: message.eventId,
        timestamp: message.timestamp,
        payload: message.payload,
      });
    },
    onRiskEvent: (message) => {
      mutableAnalyticsProvider?.updateRiskEvent(message);

      websocketHub.publish({
        type: "RISK_EVENT",
        eventId: message.eventId,
        timestamp: message.timestamp,
        payload: message.payload,
      });
    },
    onError: (error) => {
      app.log.warn({ error }, "analytics_client_error");
    },
    onStateChange: (state) => {
      app.log.info({ state }, "analytics_client_state_changed");
    },
  });

  const engineEventClient = createEngineEventClient({
    host: config.engine.host,
    port: config.engine.port,
    connectTimeoutMs: config.engine.connectTimeoutMs,
    reconnectInitialDelayMs: config.engine.reconnectInitialDelayMs,
    reconnectMaxDelayMs: config.engine.reconnectMaxDelayMs,
    reconnectMaxAttempts: config.engine.reconnectMaxAttempts,
    onEvent: (event) => {
      websocketHub.publish(event);
      analyticsClient.sendTrade(event);
    },
    onError: (error) => {
      app.log.warn(
        { error },
        "engine_event_client_error",
      );
    },
    onStateChange: (state) => {
      app.log.info(
        { state },
        "engine_event_client_state_changed",
      );
    },
  });

  app.register(websocket, {
    options: {
      maxPayload: config.websocket.maxPayloadBytes,
      clientTracking: true,
    },
  });

  app.register(async (websocketApp) => {
    websocketApp.get(
      config.websocket.path,
      { websocket: true },
      (socket) => {
        websocketHub.add(socket);
      },
    );
  });

  registerErrorHandler(app);

  app.register(cors, {
    origin: config.cors.origin,
  });

  app.register(registerHealthRoutes);

  const statusProvider =
    options.statusProvider ??
    createStatusProvider({
      isEngineConnected: engineEventClient.isConnected,
      isAnalyticsConnected: analyticsClient.isConnected,
    });

  app.register(registerV1Routes, {
    statusProvider,
    marketProvider: options.marketProvider,
    orderBookProvider: options.orderBookProvider,
    tradesProvider: options.tradesProvider,
    analyticsProvider,
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

    websocketHub.startHeartbeat();
    engineEventClient.start();
    analyticsClient.start();
    started = true;
  };

  const stop = async (): Promise<void> => {
    if (!started) {
      return;
    }

    analyticsClient.stop();
    engineEventClient.stop();
    websocketHub.stopHeartbeat();
    websocketHub.closeAll();
    await app.close();
    started = false;
  };

  return {
    app,
    config,
    start,
    stop,
    websocketHub,
    engineEventClient,
    analyticsClient,
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
