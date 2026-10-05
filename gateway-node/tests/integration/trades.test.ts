import { describe, expect, test } from "bun:test";

import { createGatewayServer } from "../../src/server.ts";
import type {
  Trade,
  TradesProvider,
  TradesState,
} from "../../src/trades/trades.types.ts";

interface ErrorResponse {
  readonly error: {
    readonly code: string;
    readonly message: string;
    readonly request_id: string;
  };
}

interface TradesResponse {
  readonly data: TradesState;
}

describe("GET /api/v1/trades", () => {
  test("returns dependency unavailable when trade history is unavailable", async () => {
    const gateway = createGatewayServer(process.env, {
      tradesProvider: {
        getTrades: () => null,
      },
    });

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/v1/trades",
    });

    expect(response.statusCode).toBe(503);

    const body = response.json() as ErrorResponse;

    expect(body.error.code).toBe("DEPENDENCY_UNAVAILABLE");
    expect(body.error.message).toBe("Required dependency is unavailable");
    expect(body.error.request_id).toBeTruthy();

    await gateway.stop();
  });

  test("returns trades from the injected provider", async () => {
    const trades: readonly Trade[] = [
      {
        tradeId: "trade-1-buy-sell",
        symbol: "SIM",
        price: 100.5,
        quantity: 5,
        takerSide: "buy",
        timestamp: "2026-10-01T10:00:00.000Z",
      },
      {
        tradeId: "trade-2-sell-buy",
        symbol: "SIM",
        price: 101,
        quantity: 3,
        takerSide: "sell",
        timestamp: "2026-10-01T10:01:00.000Z",
      },
    ];

    const tradesProvider: TradesProvider = {
      getTrades: () => ({
        trades,
      }),
    };

    const gateway = createGatewayServer(process.env, {
      tradesProvider,
    });

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/v1/trades",
    });

    expect(response.statusCode).toBe(200);

    const body = response.json() as TradesResponse;

    expect(body).toEqual({
      data: {
        trades,
      },
    });

    await gateway.stop();
  });
});
