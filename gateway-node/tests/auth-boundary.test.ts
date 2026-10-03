import { afterEach, describe, expect, test } from "bun:test";

import type { FastifyInstance } from "fastify";

import { createGatewayServer } from "../src/server.ts";

const gateways: FastifyInstance[] = [];

afterEach(async () => {
  await Promise.all(
    gateways.splice(0).map(async (app) => {
      await app.close();
    }),
  );
});

describe("authentication boundary", () => {
  test("is non-enforcing by default", async () => {
    const gateway = createGatewayServer();

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/health",
    });

    expect(response.statusCode).toBe(200);
    gateways.push(gateway.app);
  });

  test("enforces authentication only when explicitly enabled", async () => {
    const gateway = createGatewayServer({
      AUTH_ENABLED: "true",
      AUTH_ENFORCEMENT_ENABLED: "true",
    });

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/health",
    });

    expect(response.statusCode).toBe(401);
    expect(response.json()).toMatchObject({
      error: {
        code: "UNAUTHORIZED",
        message: "Authentication required",
        request_id: expect.any(String),
      },
    });
    gateways.push(gateway.app);
  });

  test("accepts a resolved principal through the future authentication seam", async () => {
    const gateway = createGatewayServer(
      {
        AUTH_ENABLED: "true",
        AUTH_ENFORCEMENT_ENABLED: "true",
      },
      {
        authenticationResolver: () => ({
          authenticated: true,
          principal: {
            subject: "user-123",
            roles: ["trader"],
            scopes: ["market:read"],
          },
        }),
      },
    );

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/health",
    });

    expect(response.statusCode).toBe(200);
    gateways.push(gateway.app);
  });
});
