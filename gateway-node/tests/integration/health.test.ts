import { describe, expect, test } from "bun:test";
import { createGatewayServer } from "../../src/server";

describe("GET /api/health", () => {
  test("returns gateway health status", async () => {
    const gateway = createGatewayServer();

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/health",
    });

    expect(response.statusCode).toBe(200);

    const body = response.json() as {
      status: string;
      service: string;
    };

    expect(body).toEqual({
      status: "ok",
      service: "gateway",
    });

    await gateway.stop();
  });
});
