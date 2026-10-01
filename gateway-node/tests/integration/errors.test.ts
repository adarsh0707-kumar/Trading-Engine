import { describe, expect, test } from "bun:test";

import { createGatewayServer } from "../../src/server.ts";
import { dependencyUnavailable } from "../../src/errors/api-error.ts";

interface ErrorResponse {
  readonly error: {
    readonly code: string;
    readonly message: string;
    readonly request_id: string;
  };
}

describe("API error handling", () => {
  test("returns a deterministic 404 error response", async () => {
    const gateway = createGatewayServer();

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/v1/does-not-exist",
    });

    expect(response.statusCode).toBe(404);

    const body = response.json() as ErrorResponse;

    expect(body.error.code).toBe("NOT_FOUND");
    expect(body.error.message).toBe("Route not found");
    expect(body.error.request_id).toBeTruthy();

    await gateway.stop();
  });

  test("maps ApiError to its declared HTTP status and code", async () => {
    const gateway = createGatewayServer();

    gateway.app.get("/api/v1/test-error", async () => {
      throw dependencyUnavailable("Trading engine is unavailable");
    });

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/v1/test-error",
    });

    expect(response.statusCode).toBe(503);

    const body = response.json() as ErrorResponse;

    expect(body.error).toEqual({
      code: "DEPENDENCY_UNAVAILABLE",
      message: "Trading engine is unavailable",
      request_id: body.error.request_id,
    });

    expect(body.error.request_id).toBeTruthy();

    await gateway.stop();
  });

  test("maps Fastify validation failures to INVALID_ARGUMENT", async () => {
    const gateway = createGatewayServer();

    gateway.app.get(
      "/api/v1/validated",
      {
        schema: {
          querystring: {
            type: "object",
            required: ["limit"],
            properties: {
              limit: {
                type: "integer",
                minimum: 1,
              },
            },
          },
        },
      },
      async () => ({
        data: {
          ok: true,
        },
      }),
    );

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/v1/validated?limit=invalid",
    });

    expect(response.statusCode).toBe(400);

    const body = response.json() as ErrorResponse;

    expect(body.error.code).toBe("INVALID_ARGUMENT");
    expect(body.error.message).toBe("Request validation failed");
    expect(body.error.request_id).toBeTruthy();

    await gateway.stop();
  });
});
