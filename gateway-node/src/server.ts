import { createLiveTradingState } from "./live-trading/live-trading-state.ts";
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
import { ApiError } from "./errors/api-error.ts";
import {
  anonymousAuthentication,
  requireAuthentication,
  type AuthenticationState,
} from "./security/auth.ts";
import { assertRateLimit, createRateLimiter } from "./security/rate-limit.ts";
import { createOperationalLogger } from "./logging/operational-logger.ts";

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
  readonly authenticationResolver?: (
    request: unknown,
  ) => AuthenticationState | Promise<AuthenticationState>;
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

  const operationalLog = createOperationalLogger(app.log, "gateway");
  const requestStartTimes = new WeakMap<object, bigint>();

  app.addHook("onRequest", async (request) => {
    requestStartTimes.set(request, process.hrtime.bigint());

    operationalLog.info("http_request_started", {
      requestId: request.id,
      method: request.method,
      path: request.url.split("?")[0] ?? "",
    });
  });

  app.addHook("onResponse", async (request, reply) => {
    const start = requestStartTimes.get(request);
    if (start !== undefined) {
      const durationSeconds =
        Number(process.hrtime.bigint() - start) / 1_000_000_000;
      metrics.observeHttpRequestDuration(request.method, durationSeconds);
    }

    metrics.recordHttpRequest(request.method, reply.statusCode);

    operationalLog.info("http_request_completed", {
      requestId: request.id,
      method: request.method,
      path: request.url.split("?")[0] ?? "",
      statusCode: reply.statusCode,
      outcome: reply.statusCode >= 500 ? "failure" : "success",
    });
  });

  const metrics = createGatewayMetrics();

  const websocketHub = createWebSocketHub({
    maxQueueSize: config.websocket.maxQueueSize,
    heartbeatIntervalMs: config.websocket.heartbeatIntervalMs,
    maxMessageBytes: config.websocket.maxPayloadBytes,
    onOperationalEvent: (event) => {
      switch (event.event) {
        case "websocket_client_connected":
          metrics.recordWebSocketConnection();
          metrics.setWebSocketClients(websocketHub.size());
          break;
        case "websocket_client_disconnected":
          metrics.recordWebSocketDisconnection();
          metrics.setWebSocketClients(websocketHub.size());
          break;
        case "websocket_subscription_updated":
          metrics.recordWebSocketSubscriptionUpdate();
          break;
        case "websocket_client_queue_overflow":
          metrics.recordWebSocketQueueOverflow();
          metrics.setWebSocketClients(websocketHub.size());
          break;
        case "websocket_client_heartbeat_timeout":
          metrics.recordWebSocketHeartbeatTimeout();
          metrics.setWebSocketClients(websocketHub.size());
          break;
      }

      const fields = {
        outcome: event.outcome,
        state: event.state,
      };

      if (event.level === "error") {
        operationalLog.error(event.event, fields);
      } else if (event.level === "warn") {
        operationalLog.warn(event.event, fields);
      } else {
        operationalLog.info(event.event, fields);
      }
    },
  });

  const authenticationResolver =
    options.authenticationResolver ?? (() => anonymousAuthentication());

  const rateLimiter = createRateLimiter({
    enabled: config.rateLimit.enabled,
    maxRequests: config.rateLimit.maxRequests,
    windowMs: config.rateLimit.windowMs,
    maxClients: config.rateLimit.maxClients,
  });

  app.addHook("onRequest", async (request) => {
    const path = request.url.split("?")[0] ?? "";
    const rateLimitExcluded =
      config.rateLimit.excludedPaths.includes(path) ||
      path === config.websocket.path;

    if (!rateLimitExcluded) {
      try {
        assertRateLimit(rateLimiter, request.ip ?? "unknown");
      } catch (error) {
        if (error instanceof ApiError && error.code === "RATE_LIMITED") {
          metrics.recordRateLimitRejection();
          app.log.warn(
            { ip: request.ip, method: request.method, url: request.url },
            "gateway_rate_limit_rejected",
          );
        }
        throw error;
      }
    }

    if (config.auth.enabled && config.auth.enforcementEnabled) {
      const authentication = await authenticationResolver(request);
      requireAuthentication(authentication);
    }
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
      metrics.recordAnalyticsUpdate();
      metrics.recordWebSocketPublishedEvent("ANALYTICS_UPDATE");
      mutableAnalyticsProvider?.updateAnalytics(message);

      operationalLog.info("analytics_update_received", {
        eventId: message.eventId,
        requestId: message.requestId,
        outcome: "accepted",
      });

      websocketHub.publish({
        type: "ANALYTICS_UPDATE",
        eventId: message.eventId,
        requestId: message.requestId,
        timestamp: message.timestamp,
        payload: message.payload,
      });
    },
    onRiskEvent: (message) => {
      metrics.recordAnalyticsRiskEvent();
      metrics.recordWebSocketPublishedEvent("RISK_EVENT");
      mutableAnalyticsProvider?.updateRiskEvent(message);

      operationalLog.info("analytics_risk_event_received", {
        eventId: message.eventId,
        requestId: message.requestId,
        outcome: "accepted",
      });

      websocketHub.publish({
        type: "RISK_EVENT",
        eventId: message.eventId,
        requestId: message.requestId,
        timestamp: message.timestamp,
        payload: message.payload,
      });
    },
    onError: (error) => {
      metrics.recordAnalyticsError();
      operationalLog.warn("analytics_client_error", { outcome: "failure", error });
    },
    onStateChange: (state) => {
      metrics.recordAnalyticsState(state);
      const status = statusProvider.getStatus();
      metrics.setGatewayReadiness(
        status.engine === "connected" && status.analytics === "connected",
      );
      operationalLog.info("analytics_client_state_changed", { state });
    },
    onHealthEvent: ({ type }) => {
      switch (type) {
        case "queue_overflow":
          metrics.recordAnalyticsQueueOverflow();
          operationalLog.warn("analytics_outbound_queue_overflow", { outcome: "degraded" });
          break;
      }
    },
  });

  const liveTradingState = createLiveTradingState();

  const engineEventClient = createEngineEventClient({
    host: config.engine.host,
    port: config.engine.port,
    connectTimeoutMs: config.engine.connectTimeoutMs,
    heartbeatTimeoutMs: config.engine.heartbeatTimeoutMs,
    reconnectInitialDelayMs: config.engine.reconnectInitialDelayMs,
    reconnectMaxDelayMs: config.engine.reconnectMaxDelayMs,
    reconnectMaxAttempts: config.engine.reconnectMaxAttempts,
    onEvent: (event) => {
      liveTradingState.onTrade(event);
      metrics.recordEngineTrade();
      operationalLog.info("engine_trade_event", {
        eventId: event.eventId,
        requestId: event.requestId,
        outcome: "accepted",
      });
      websocketHub.publish(event);
      metrics.recordWebSocketPublishedEvent(event.type);
      const sentToAnalytics = analyticsClient.sendTrade(event);
      if (sentToAnalytics) {
        metrics.recordAnalyticsTradeSent();
      } else {
        metrics.recordAnalyticsTradeSendFailure();
      }
    },
    onError: (error) => {
      operationalLog.warn("engine_event_client_error", { outcome: "failure", error });
    },
    onStateChange: (state) => {
      metrics.recordEngineState(state);
      const status = statusProvider.getStatus();
      metrics.setGatewayReadiness(
        status.engine === "connected" && status.analytics === "connected",
      );
      operationalLog.info("engine_event_client_state_changed", { state });
    },
    onHealthEvent: ({ type, timestamp }) => {
      switch (type) {
        case "message":
          metrics.recordEngineMessage();
          metrics.setEngineLastMessageAt(timestamp);
          break;
        case "heartbeat":
          metrics.recordEngineHeartbeat();
          metrics.setEngineLastHeartbeatAt(timestamp);
          break;
        case "reconnect_attempt":
          metrics.recordEngineReconnectAttempt();
          operationalLog.warn("engine_reconnect_attempt", { outcome: "degraded" });
          break;
        case "connection_failure":
          metrics.recordEngineConnectionFailure();
          operationalLog.error("engine_connection_failure", { outcome: "failure" });
          break;
        case "protocol_failure":
          metrics.recordEngineProtocolFailure();
          operationalLog.error("engine_protocol_failure", { outcome: "failure" });
          break;
        case "timeout_failure":
          metrics.recordEngineTimeoutFailure();
          operationalLog.error("engine_timeout_failure", { outcome: "failure" });
          break;
        case "liveness_timeout":
          metrics.recordEngineLivenessFailure();
          operationalLog.error("engine_liveness_timeout", { outcome: "failure" });
          break;
      }
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
    origin: [...config.cors.origins],
    credentials: false,
  });

  const statusProvider =
    options.statusProvider ??
    createStatusProvider({
      isEngineConnected: engineEventClient.isConnected,
      isAnalyticsConnected: analyticsClient.isConnected,
    });

  app.register(registerHealthRoutes, {
    statusProvider,
    onReadinessChange: (ready) => {
      metrics.setGatewayReadiness(ready);
    },
  });

  app.register(registerV1Routes, {
    statusProvider,
    marketProvider: options.marketProvider ?? liveTradingState,
    orderBookProvider: options.orderBookProvider,
    tradesProvider: options.tradesProvider ?? liveTradingState,
    analyticsProvider,
    engineProvider: options.engineProvider,
    engineEventClient,
  });

  if (config.metrics.enabled) {
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
    operationalLog.info("gateway_started", {
      outcome: "success",
      host: config.gateway.host,
      port: config.gateway.port,
    });
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
    operationalLog.info("gateway_stopping", { outcome: "requested" });
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
