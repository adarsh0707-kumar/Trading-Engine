import { afterEach, describe, expect, test } from "bun:test";

import { createGatewayServer } from "../src/server.ts";

const gateways: ReturnType<typeof createGatewayServer>[] = [];

afterEach(async () => {
  await Promise.all(
    gateways.map(async (gateway) => {
      await gateway.app.close();
    }),
  );
  gateways.length = 0;
});

describe("Gateway CORS policy", () => {
  test("adds CORS headers for an allowed origin", async () => {
    const gateway = createGatewayServer({
      CORS_ORIGINS: "https://app.example.com,https://admin.example.com",
    });
    gateways.push(gateway);

    const response = await gateway.app.inject({
      method: "GET",
      url: "/health",
      headers: {
        origin: "https://app.example.com",
      },
    });

    expect(response.statusCode).toBe(200);
    expect(response.headers["access-control-allow-origin"]).toBe(
      "https://app.example.com",
    );
    expect(response.headers["access-control-allow-credentials"]).toBeUndefined();
    expect(response.headers.vary).toContain("Origin");
  });

  test("does not add CORS headers for an untrusted origin", async () => {
    const gateway = createGatewayServer({
      CORS_ORIGINS: "https://app.example.com",
    });
    gateways.push(gateway);

    const response = await gateway.app.inject({
      method: "GET",
      url: "/health",
      headers: {
        origin: "https://evil.example.com",
      },
    });

    expect(response.statusCode).toBe(200);
    expect(response.headers["access-control-allow-origin"]).toBeUndefined();
  });

  test("supports preflight for an allowed origin", async () => {
    const gateway = createGatewayServer({
      CORS_ORIGINS: "https://app.example.com",
    });
    gateways.push(gateway);

    const response = await gateway.app.inject({
      method: "OPTIONS",
      url: "/api/v1/status",
      headers: {
        origin: "https://app.example.com",
        "access-control-request-method": "GET",
      },
    });

    expect(response.statusCode).toBe(204);
    expect(response.headers["access-control-allow-origin"]).toBe(
      "https://app.example.com",
    );
  });
});
