import { describe, expect, test } from "bun:test";

import { loadConfig } from "../src/config/config.ts";

describe("gateway analytics configuration", () => {
  test("loads the default CORS origin allowlist", () => {
    const config = loadConfig({});

    expect(config.cors.origins).toEqual(["http://localhost:5173"]);
  });

  test("loads a comma-separated CORS origin allowlist", () => {
    const config = loadConfig({
      CORS_ORIGINS: "https://app.example.com, https://admin.example.com",
    });

    expect(config.cors.origins).toEqual([
      "https://app.example.com",
      "https://admin.example.com",
    ]);
  });

  test("rejects wildcard CORS configuration", () => {
    expect(() =>
      loadConfig({
        CORS_ORIGINS: "*",
      }),
    ).toThrow("Invalid CORS origin");
  });

  test("loads the engine heartbeat liveness timeout default", () => {
    const config = loadConfig({});

    expect(config.engine.heartbeatTimeoutMs).toBe(15000);
  });

  test("loads the engine heartbeat liveness timeout override", () => {
    const config = loadConfig({
      ENGINE_HEARTBEAT_TIMEOUT_MS: "25000",
    });

    expect(config.engine.heartbeatTimeoutMs).toBe(25000);
  });

  test("loads analytics transport defaults", () => {
    const config = loadConfig({});

    expect(config.analytics).toEqual({
      host: "127.0.0.1",
      port: 8000,
      requestTimeoutMs: 5000,
      connectTimeoutMs: 5000,
      reconnectInitialDelayMs: 500,
      reconnectMaxDelayMs: 10000,
      reconnectMaxAttempts: 10,
      maxQueueSize: 256,
    });
  });

  test("loads and validates analytics transport overrides", () => {
    const config = loadConfig({
      ANALYTICS_HOST: "analytics",
      ANALYTICS_PORT: "8100",
      ANALYTICS_REQUEST_TIMEOUT_MS: "7000",
      ANALYTICS_CONNECT_TIMEOUT_MS: "6000",
      ANALYTICS_RECONNECT_INITIAL_DELAY_MS: "100",
      ANALYTICS_RECONNECT_MAX_DELAY_MS: "2000",
      ANALYTICS_RECONNECT_MAX_ATTEMPTS: "4",
      ANALYTICS_MAX_QUEUE_SIZE: "512",
    });

    expect(config.analytics).toEqual({
      host: "analytics",
      port: 8100,
      requestTimeoutMs: 7000,
      connectTimeoutMs: 6000,
      reconnectInitialDelayMs: 100,
      reconnectMaxDelayMs: 2000,
      reconnectMaxAttempts: 4,
      maxQueueSize: 512,
    });
  });

  test("rejects invalid analytics reconnect bounds", () => {
    expect(() =>
      loadConfig({
        ANALYTICS_RECONNECT_INITIAL_DELAY_MS: "2000",
        ANALYTICS_RECONNECT_MAX_DELAY_MS: "1000",
      }),
    ).toThrow(
      "ANALYTICS_RECONNECT_INITIAL_DELAY_MS must be less than or equal to ANALYTICS_RECONNECT_MAX_DELAY_MS",
    );
  });
});
