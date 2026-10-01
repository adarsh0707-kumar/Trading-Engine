import { describe, expect, test } from "bun:test";

import { createGatewayServer } from "../../src/server.ts";
import type { EngineProvider } from "../../src/engine/engine.types.ts";

interface ErrorResponse {
  readonly error: {
    readonly code: string;
    readonly message: string;
    readonly request_id: string;
  };
}

interface EngineResponse {
  readonly data: {
    readonly action: "start" | "stop" | "reset";
    readonly status: "accepted";
  };
}

describe("POST /api/v1/engine/*", () => {
  test("returns dependency unavailable when engine control is unavailable", async () => {
    const gateway = createGatewayServer();

    for (const action of ["start", "stop", "reset"] as const) {
      const response = await gateway.app.inject({
        method: "POST",
        url: `/api/v1/engine/${action}`,
      });

      expect(response.statusCode).toBe(503);

      const body = response.json() as ErrorResponse;

      expect(body.error.code).toBe("DEPENDENCY_UNAVAILABLE");
      expect(body.error.message).toBe("Engine control is unavailable");
      expect(body.error.request_id).toBeTruthy();
    }

    await gateway.stop();
  });

  test("returns accepted for supported provider actions", async () => {
    const engineProvider: EngineProvider = {
      start: () => ({
        action: "start",
        status: "accepted",
      }),
      stop: () => ({
        action: "stop",
        status: "accepted",
      }),
      reset: () => ({
        action: "reset",
        status: "accepted",
      }),
    };

    const gateway = createGatewayServer(process.env, {
      engineProvider,
    });

    for (const action of ["start", "stop", "reset"] as const) {
      const response = await gateway.app.inject({
        method: "POST",
        url: `/api/v1/engine/${action}`,
      });

      expect(response.statusCode).toBe(202);

      const body = response.json() as EngineResponse;

      expect(body).toEqual({
        data: {
          action,
          status: "accepted",
        },
      });
    }

    await gateway.stop();
  });

  test("rejects unexpected request body fields", async () => {
    const gateway = createGatewayServer();

    const response = await gateway.app.inject({
      method: "POST",
      url: "/api/v1/engine/start",
      payload: {
        unexpected: true,
      },
    });

    expect(response.statusCode).toBe(400);

    const body = response.json() as ErrorResponse;

    expect(body.error.code).toBe("INVALID_ARGUMENT");
    expect(body.error.message).toBe("Request validation failed");
    expect(body.error.request_id).toBeTruthy();

    await gateway.stop();
  });
});
