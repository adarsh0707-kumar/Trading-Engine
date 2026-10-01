import { describe, expect, test } from "bun:test";

import { createGatewayServer } from "../../src/server.ts";
import type {
  MarketProvider,
  MarketState,
} from "../../src/market/market.types.ts";

interface ErrorResponse {
  readonly error: {
    readonly code: string;
    readonly message: string;
    readonly request_id: string;
  };
}

interface MarketResponse {
  readonly data: MarketState;
}

describe("GET /api/v1/market", () => {
  test("returns dependency unavailable when market state is unavailable", async () => {
    const gateway = createGatewayServer();

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/v1/market",
    });

    expect(response.statusCode).toBe(503);

    const body = response.json() as ErrorResponse;

    expect(body.error.code).toBe("DEPENDENCY_UNAVAILABLE");
    expect(body.error.message).toBe("Market state is unavailable");
    expect(body.error.request_id).toBeTruthy();

    await gateway.stop();
  });

  test("returns the market state from the injected provider", async () => {
    const marketProvider: MarketProvider = {
      getMarket: () => ({
        symbol: "SIM",
        lastPrice: 101.25,
        lastQuantity: 5,
        timestamp: "2026-10-01T10:00:00.000Z",
      }),
    };

    const gateway = createGatewayServer(process.env, {
      marketProvider,
    });

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/v1/market",
    });

    expect(response.statusCode).toBe(200);

    const body = response.json() as MarketResponse;

    expect(body).toEqual({
      data: {
        symbol: "SIM",
        lastPrice: 101.25,
        lastQuantity: 5,
        timestamp: "2026-10-01T10:00:00.000Z",
      },
    });

    await gateway.stop();
  });
});
