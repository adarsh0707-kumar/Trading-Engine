import { describe, expect, test } from "bun:test";

import { createGatewayServer } from "../../src/server.ts";
import type { StatusProvider } from "../../src/status/status.types.ts";

interface StatusResponse {
  readonly data: {
    readonly gateway: "ok";
    readonly engine: "connected" | "disconnected";
    readonly analytics: "connected" | "disconnected";
  };
}

describe("GET /api/v1/status", () => {
  test("returns the current gateway dependency status", async () => {
    const gateway = createGatewayServer();

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/v1/status",
    });

    expect(response.statusCode).toBe(200);

    const body = response.json() as StatusResponse;

    expect(body).toEqual({
      data: {
        gateway: "ok",
        engine: "disconnected",
        analytics: "disconnected",
      },
    });

    await gateway.stop();
  });

  test("uses the injected status provider", async () => {
    const statusProvider: StatusProvider = {
      getStatus: () => ({
        gateway: "ok",
        engine: "connected",
        analytics: "connected",
      }),
    };

    const gateway = createGatewayServer(process.env, {
      statusProvider,
    });

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/v1/status",
    });

    expect(response.statusCode).toBe(200);

    const body = response.json() as StatusResponse;

    expect(body).toEqual({
      data: {
        gateway: "ok",
        engine: "connected",
        analytics: "connected",
      },
    });

    const engineHealthResponse = await gateway.app.inject({
      method: "GET",
      url: "/api/v1/status/engine",
    });

    expect(engineHealthResponse.statusCode).toBe(200);
    expect(engineHealthResponse.json()).toEqual({
      data: {
        state: "disconnected",
        connectedAt: null,
        lastMessageAt: null,
        lastHeartbeatAt: null,
        reconnectAttempts: 0,
      },
    });

    await gateway.stop();
  });
});
