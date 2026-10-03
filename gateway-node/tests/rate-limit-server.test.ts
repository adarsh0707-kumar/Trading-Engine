import { afterEach, describe, expect, test } from "bun:test";

import type { FastifyInstance } from "fastify";

import { createGatewayServer } from "../src/server.ts";

const gateways: Array<{ readonly app: FastifyInstance; readonly stop: () => Promise<void> }> = [];

afterEach(async () => {
  await Promise.all(gateways.splice(0).map(async (gateway) => {
    await gateway.stop();
    await gateway.app.close();
  }));
});

describe("HTTP rate limit boundary", () => {
  test("returns 429 with a stable public contract after the limit is reached", async () => {
    const gateway = createGatewayServer({
      RATE_LIMIT_MAX_REQUESTS: "2",
      RATE_LIMIT_WINDOW_MS: "60000",
    });
    gateways.push(gateway);

    const first = await gateway.app.inject({
      method: "GET",
      url: "/does-not-exist",
    });
    const second = await gateway.app.inject({
      method: "GET",
      url: "/does-not-exist",
    });
    const third = await gateway.app.inject({
      method: "GET",
      url: "/does-not-exist",
    });

    expect(first.statusCode).toBe(404);
    expect(second.statusCode).toBe(404);
    expect(third.statusCode).toBe(429);
    expect(third.headers["retry-after"]).toBe("60");
    expect(third.json()).toMatchObject({
      error: {
        code: "RATE_LIMITED",
        message: "Too many requests",
        request_id: expect.any(String),
      },
    });
  });

  test("does not rate-limit excluded health endpoint", async () => {
    const gateway = createGatewayServer({
      RATE_LIMIT_MAX_REQUESTS: "1",
      RATE_LIMIT_WINDOW_MS: "60000",
    });
    gateways.push(gateway);

    const responses = await Promise.all(
      Array.from({ length: 5 }, () =>
        gateway.app.inject({
          method: "GET",
          url: "/api/health",
        }),
      ),
    );

    expect(responses.every((response) => response.statusCode === 200)).toBe(true);
  });

  test("can be disabled without changing endpoint behavior", async () => {
    const gateway = createGatewayServer({
      RATE_LIMIT_ENABLED: "false",
      RATE_LIMIT_MAX_REQUESTS: "1",
      RATE_LIMIT_WINDOW_MS: "60000",
    });
    gateways.push(gateway);

    const first = await gateway.app.inject({
      method: "GET",
      url: "/does-not-exist",
    });
    const second = await gateway.app.inject({
      method: "GET",
      url: "/does-not-exist",
    });

    expect(first.statusCode).toBe(404);
    expect(second.statusCode).toBe(404);
  });

  test("increments the rate limit rejection metric", async () => {
    const gateway = createGatewayServer({
      RATE_LIMIT_MAX_REQUESTS: "1",
      RATE_LIMIT_WINDOW_MS: "60000",
    });
    gateways.push(gateway);

    await gateway.app.inject({
      method: "GET",
      url: "/does-not-exist",
    });
    await gateway.app.inject({
      method: "GET",
      url: "/does-not-exist",
    });

    const metrics = await gateway.app.inject({
      method: "GET",
      url: "/metrics",
    });

    expect(metrics.statusCode).toBe(200);
    expect(metrics.body).toContain("gateway_rate_limit_rejections_total");
  });
});
