import { describe, expect, test } from "bun:test";

import { loadConfig } from "../../src/config/config.ts";

describe("loadConfig", () => {
  test("uses defaults when environment variables are absent", () => {
    const config = loadConfig({});

    expect(config.gateway.host).toBe("127.0.0.1");
    expect(config.gateway.port).toBe(8080);

    expect(config.engine.host).toBe("127.0.0.1");
    expect(config.engine.port).toBe(9000);

    expect(config.analytics.host).toBe("127.0.0.1");
    expect(config.analytics.port).toBe(8000);

    expect(config.websocket.path).toBe("/ws");
    expect(config.websocket.heartbeatIntervalMs).toBe(30000);
    expect(config.websocket.maxPayloadBytes).toBe(1024 * 1024);

    expect(config.http.requestTimeoutMs).toBe(10000);
    expect(config.http.bodyLimitBytes).toBe(1024 * 1024);

    expect(config.logging.level).toBe("info");

    expect(config.metrics.enabled).toBe(true);
    expect(config.metrics.path).toBe("/metrics");

    expect(config.cors.origins).toEqual(["http://localhost:5173"]);

    expect(config.rateLimit.enabled).toBe(true);
    expect(config.rateLimit.maxRequests).toBe(120);
    expect(config.rateLimit.windowMs).toBe(60_000);
    expect(config.rateLimit.maxClients).toBe(10_000);
    expect(config.rateLimit.excludedPaths).toEqual(["/api/health", "/metrics"]);
  });

  test("loads gateway, engine, and analytics values from environment", () => {
    const config = loadConfig({
      GATEWAY_HOST: "0.0.0.0",
      GATEWAY_PORT: "9090",
      ENGINE_HOST: "engine",
      ENGINE_PORT: "9100",
      ANALYTICS_HOST: "analytics",
      ANALYTICS_PORT: "8100",
    });

    expect(config.gateway.host).toBe("0.0.0.0");
    expect(config.gateway.port).toBe(9090);

    expect(config.engine.host).toBe("engine");
    expect(config.engine.port).toBe(9100);

    expect(config.analytics.host).toBe("analytics");
    expect(config.analytics.port).toBe(8100);
  });

  test("loads timeout and reconnect configuration", () => {
    const config = loadConfig({
      ENGINE_CONNECT_TIMEOUT_MS: "2500",
      ENGINE_REQUEST_TIMEOUT_MS: "3000",
      ENGINE_RECONNECT_INITIAL_DELAY_MS: "250",
      ENGINE_RECONNECT_MAX_DELAY_MS: "15000",
      ENGINE_RECONNECT_MAX_ATTEMPTS: "5",
      ANALYTICS_REQUEST_TIMEOUT_MS: "4000",
    });

    expect(config.engine.connectTimeoutMs).toBe(2500);
    expect(config.engine.requestTimeoutMs).toBe(3000);
    expect(config.engine.reconnectInitialDelayMs).toBe(250);
    expect(config.engine.reconnectMaxDelayMs).toBe(15000);
    expect(config.engine.reconnectMaxAttempts).toBe(5);
    expect(config.analytics.requestTimeoutMs).toBe(4000);
  });

  test("freezes the top-level configuration", () => {
    const config = loadConfig();

    expect(Object.isFrozen(config)).toBe(true);
  });

  test("freezes all nested configuration sections", () => {
    const config = loadConfig();

    expect(Object.isFrozen(config.gateway)).toBe(true);
    expect(Object.isFrozen(config.engine)).toBe(true);
    expect(Object.isFrozen(config.analytics)).toBe(true);
    expect(Object.isFrozen(config.websocket)).toBe(true);
    expect(Object.isFrozen(config.http)).toBe(true);
    expect(Object.isFrozen(config.logging)).toBe(true);
    expect(Object.isFrozen(config.metrics)).toBe(true);
    expect(Object.isFrozen(config.cors)).toBe(true);
  });

  test("loads HTTP, WebSocket, logging, metrics, and CORS configuration", () => {
    const config = loadConfig({
      WEBSOCKET_PATH: "/stream",
      WEBSOCKET_HEARTBEAT_INTERVAL_MS: "15000",
      WEBSOCKET_MAX_PAYLOAD_BYTES: "2048",
      HTTP_REQUEST_TIMEOUT_MS: "7000",
      HTTP_BODY_LIMIT_BYTES: "4096",
      LOG_LEVEL: "debug",
      METRICS_ENABLED: "false",
      METRICS_PATH: "/internal/metrics",
      CORS_ORIGIN: "https://example.com",
      RATE_LIMIT_ENABLED: "false",
      RATE_LIMIT_MAX_REQUESTS: "25",
      RATE_LIMIT_WINDOW_MS: "5000",
      RATE_LIMIT_MAX_CLIENTS: "500",
    });

    expect(config.websocket.path).toBe("/stream");
    expect(config.websocket.heartbeatIntervalMs).toBe(15000);
    expect(config.websocket.maxPayloadBytes).toBe(2048);

    expect(config.http.requestTimeoutMs).toBe(7000);
    expect(config.http.bodyLimitBytes).toBe(4096);

    expect(config.logging.level).toBe("debug");

    expect(config.metrics.enabled).toBe(false);
    expect(config.metrics.path).toBe("/internal/metrics");

    expect(config.cors.origins).toEqual(["https://example.com"]);
    expect(config.rateLimit.enabled).toBe(false);
    expect(config.rateLimit.maxRequests).toBe(25);
    expect(config.rateLimit.windowMs).toBe(5000);
    expect(config.rateLimit.maxClients).toBe(500);
  });

  test("rejects invalid ports", () => {
    expect(() =>
      loadConfig({
        GATEWAY_PORT: "70000",
      }),
    ).toThrow("Invalid GATEWAY_PORT");

    expect(() =>
      loadConfig({
        ENGINE_PORT: "0",
      }),
    ).toThrow("Invalid ENGINE_PORT");
  });

  test("accepts valid host values", () => {
    const config = loadConfig({
      GATEWAY_HOST: "0.0.0.0",
      ENGINE_HOST: "engine",
      ANALYTICS_HOST: "analytics.internal",
    });

    expect(config.gateway.host).toBe("0.0.0.0");
    expect(config.engine.host).toBe("engine");
    expect(config.analytics.host).toBe("analytics.internal");
  });

  test("rejects invalid host values", () => {
    expect(() =>
      loadConfig({
        GATEWAY_HOST: "invalid host",
      }),
    ).toThrow("Invalid GATEWAY_HOST");

    expect(() =>
      loadConfig({
        ENGINE_HOST: "engine host",
      }),
    ).toThrow("Invalid ENGINE_HOST");

    expect(() =>
      loadConfig({
        ANALYTICS_HOST: "analytics..internal",
      }),
    ).toThrow("Invalid ANALYTICS_HOST");

    expect(() =>
      loadConfig({
        GATEWAY_HOST: "-invalid",
      }),
    ).toThrow("Invalid GATEWAY_HOST");
  });

  test("rejects invalid numeric settings", () => {
    expect(() =>
      loadConfig({
        HTTP_BODY_LIMIT_BYTES: "0",
      }),
    ).toThrow("HTTP_BODY_LIMIT_BYTES must be a positive integer");

    expect(() =>
      loadConfig({
        ENGINE_RECONNECT_MAX_ATTEMPTS: "-1",
      }),
    ).toThrow("Invalid ENGINE_RECONNECT_MAX_ATTEMPTS");
  });

  test("rejects reconnect delays when the initial delay exceeds the maximum", () => {
    expect(() =>
      loadConfig({
        ENGINE_RECONNECT_INITIAL_DELAY_MS: "15000",
        ENGINE_RECONNECT_MAX_DELAY_MS: "10000",
      }),
    ).toThrow(
      "ENGINE_RECONNECT_INITIAL_DELAY_MS must be less than or equal to ENGINE_RECONNECT_MAX_DELAY_MS",
    );
  });

  test("accepts equal reconnect initial and maximum delays", () => {
    const config = loadConfig({
      ENGINE_RECONNECT_INITIAL_DELAY_MS: "10000",
      ENGINE_RECONNECT_MAX_DELAY_MS: "10000",
    });

    expect(config.engine.reconnectInitialDelayMs).toBe(10000);
    expect(config.engine.reconnectMaxDelayMs).toBe(10000);
  });

  test("rejects rate limit values outside their configured bounds", () => {
    expect(() => loadConfig({ RATE_LIMIT_MAX_REQUESTS: "0" })).toThrow(
      "RATE_LIMIT_MAX_REQUESTS must be a positive integer",
    );

    expect(() => loadConfig({ RATE_LIMIT_MAX_REQUESTS: "10001" })).toThrow(
      "RATE_LIMIT_MAX_REQUESTS must not exceed 10000",
    );

    expect(() => loadConfig({ RATE_LIMIT_WINDOW_MS: "3600001" })).toThrow(
      "RATE_LIMIT_WINDOW_MS must not exceed 3600000",
    );

    expect(() => loadConfig({ RATE_LIMIT_MAX_CLIENTS: "100001" })).toThrow(
      "RATE_LIMIT_MAX_CLIENTS must not exceed 100000",
    );
  });

  test("rejects invalid boolean settings", () => {
    expect(() =>
      loadConfig({
        METRICS_ENABLED: "yes",
      }),
    ).toThrow("Invalid METRICS_ENABLED");
  });

  test("rejects paths that do not start with a slash", () => {
    expect(() =>
      loadConfig({
        WEBSOCKET_PATH: "ws",
      }),
    ).toThrow("Invalid WEBSOCKET_PATH");

    expect(() =>
      loadConfig({
        METRICS_PATH: "metrics",
      }),
    ).toThrow("Invalid METRICS_PATH");
  });

  test("trims environment values", () => {
    const config = loadConfig({
      GATEWAY_HOST: "  0.0.0.0  ",
      GATEWAY_PORT: " 9090 ",
      LOG_LEVEL: " debug ",
    });

    expect(config.gateway.host).toBe("0.0.0.0");
    expect(config.gateway.port).toBe(9090);
    expect(config.logging.level).toBe("debug");
  });
});
