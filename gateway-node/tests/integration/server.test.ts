import { describe, expect, test } from "bun:test";
import { createGatewayServer } from "../../src/server.ts";

describe("gateway server lifecycle", () => {
  test("starts and stops cleanly", async () => {
    const gateway = createGatewayServer();

    await expect(gateway.start()).resolves.toBeUndefined();
    await expect(gateway.stop()).resolves.toBeUndefined();
  });

  test("start and stop are idempotent", async () => {
    const gateway = createGatewayServer();

    await gateway.start();
    await gateway.start();

    await gateway.stop();
    await gateway.stop();
  });
});

describe("gateway server CORS", () => {
  test("returns the configured CORS origin", async () => {
    const gateway = createGatewayServer({
      ...process.env,
      CORS_ORIGIN: "http://localhost:3000",
    });

    const response = await gateway.app.inject({
      method: "OPTIONS",
      url: "/health",
      headers: {
        origin: "http://localhost:3000",
        "access-control-request-method": "GET",
      },
    });

    expect(response.statusCode).toBe(204);
    expect(response.headers["access-control-allow-origin"]).toBe(
      "http://localhost:3000",
    );

    await gateway.stop();
  });
});

describe("gateway server metrics", () => {
  test("serves Prometheus metrics on the configured path", async () => {
    const gateway = createGatewayServer({
      ...process.env,
      METRICS_ENABLED: "true",
      METRICS_PATH: "/custom-metrics",
    });

    const response = await gateway.app.inject({
      method: "GET",
      url: "/custom-metrics",
    });

    expect(response.statusCode).toBe(200);
    expect(response.headers["content-type"]).toContain("text/plain");
    expect(response.body).toContain("# HELP");

    const defaultPathResponse = await gateway.app.inject({
      method: "GET",
      url: "/metrics",
    });

    expect(defaultPathResponse.statusCode).toBe(404);

    await gateway.stop();
  });

  test("does not expose metrics when disabled", async () => {
    const gateway = createGatewayServer({
      ...process.env,
      METRICS_ENABLED: "false",
      METRICS_PATH: "/metrics",
    });

    const response = await gateway.app.inject({
      method: "GET",
      url: "/metrics",
    });

    expect(response.statusCode).toBe(404);

    await gateway.stop();
  });
});
