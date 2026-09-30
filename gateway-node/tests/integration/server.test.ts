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
