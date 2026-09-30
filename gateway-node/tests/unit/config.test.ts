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
    expect(config.websocket.maxPayloadBytes).toBe(1024 * 1024);

    expect(config.http.bodyLimitBytes).toBe(1024 * 1024);

    expect(config.logging.level).toBe("info");

    expect(config.metrics.enabled).toBe(true);
    expect(config.metrics.path).toBe("/metrics");

    expect(config.cors.origin).toBe("http://localhost:5173");
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
    });

    expect(config.websocket.path).toBe("/stream");
    expect(config.websocket.heartbeatIntervalMs).toBe(15000);
    expect(config.websocket.maxPayloadBytes).toBe(2048);

    expect(config.http.requestTimeoutMs).toBe(7000);
    expect(config.http.bodyLimitBytes).toBe(4096);

    expect(config.logging.level).toBe("debug");

    expect(config.metrics.enabled).toBe(false);
    expect(config.metrics.path).toBe("/internal/metrics");

    expect(config.cors.origin).toBe("https://example.com");
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

  test("rejects invalid numeric settings", () => {
    expect(() =>
      loadConfig({
        HTTP_BODY_LIMIT_BYTES: "0",
      }),
    ).toThrow("Invalid HTTP_BODY_LIMIT_BYTES");

    expect(() =>
      loadConfig({
        ENGINE_RECONNECT_MAX_ATTEMPTS: "-1",
      }),
    ).toThrow("Invalid ENGINE_RECONNECT_MAX_ATTEMPTS");
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
