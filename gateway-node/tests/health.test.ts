import Fastify from "fastify";
import { describe, expect, test } from "bun:test";

import { registerHealthRoutes } from "../src/api/health.ts";

describe("health routes", () => {
  test("liveness reports gateway process health", async () => {
    const app = Fastify();

    await registerHealthRoutes(app, {
      statusProvider: {
        getStatus: () => ({
        gateway: "ok",
        engine: "disconnected",
        analytics: "disconnected",
        }),
      },
    });

    const response = await app.inject({
      method: "GET",
      url: "/api/health",
    });

    expect(response.statusCode).toBe(200);
    expect(JSON.parse(response.body)).toEqual({
      status: "ok",
      service: "gateway",
    });

    await app.close();
  });

  test("readiness is healthy only when required dependencies are connected", async () => {
    const app = Fastify();

    await registerHealthRoutes(app, {
      getStatus: () => ({
        gateway: "ok",
        engine: "connected",
        analytics: "connected",
      }),
    });

    const response = await app.inject({
      method: "GET",
      url: "/api/ready",
    });

    expect(response.statusCode).toBe(200);
    expect(JSON.parse(response.body)).toEqual({
      status: "ready",
      service: "gateway",
      dependencies: {
        gateway: "ok",
        engine: "connected",
        analytics: "connected",
      },
    });

    await app.close();
  });

  test("readiness returns 503 when a required dependency is unavailable", async () => {
    const app = Fastify();

    await registerHealthRoutes(app, {
      getStatus: () => ({
        gateway: "ok",
        engine: "disconnected",
        analytics: "connected",
      }),
    });

    const response = await app.inject({
      method: "GET",
      url: "/api/ready",
    });

    expect(response.statusCode).toBe(503);
    expect(JSON.parse(response.body)).toEqual({
      status: "not_ready",
      service: "gateway",
      dependencies: {
        gateway: "ok",
        engine: "disconnected",
        analytics: "connected",
      },
    });

    await app.close();
  });
});
