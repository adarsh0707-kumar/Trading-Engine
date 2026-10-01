import { describe, expect, test } from "bun:test";

import { createGatewayServer } from "../../src/server.ts";
import type {
  OrderBookProvider,
  OrderBookState,
} from "../../src/orderbook/orderbook.types.ts";

interface ErrorResponse {
  readonly error: {
    readonly code: string;
    readonly message: string;
    readonly request_id: string;
  };
}

interface OrderBookResponse {
  readonly data: OrderBookState;
}

describe("GET /api/v1/orderbook", () => {
  test("returns dependency unavailable when order book state is unavailable", async () => {
    const gateway = createGatewayServer();

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/v1/orderbook",
    });

    expect(response.statusCode).toBe(503);

    const body = response.json() as ErrorResponse;

    expect(body.error.code).toBe("DEPENDENCY_UNAVAILABLE");
    expect(body.error.message).toBe("Order book state is unavailable");
    expect(body.error.request_id).toBeTruthy();

    await gateway.stop();
  });

  test("returns the order book from the injected provider", async () => {
    const orderBookProvider: OrderBookProvider = {
      getOrderBook: () => ({
        symbol: "SIM",
        bids: [
          {
            price: 100,
            quantity: 10,
          },
          {
            price: 99.5,
            quantity: 20,
          },
        ],
        asks: [
          {
            price: 100.5,
            quantity: 15,
          },
          {
            price: 101,
            quantity: 25,
          },
        ],
        timestamp: "2026-10-01T10:00:00.000Z",
      }),
    };

    const gateway = createGatewayServer(process.env, {
      orderBookProvider,
    });

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/v1/orderbook",
    });

    expect(response.statusCode).toBe(200);

    const body = response.json() as OrderBookResponse;

    expect(body).toEqual({
      data: {
        symbol: "SIM",
        bids: [
          {
            price: 100,
            quantity: 10,
          },
          {
            price: 99.5,
            quantity: 20,
          },
        ],
        asks: [
          {
            price: 100.5,
            quantity: 15,
          },
          {
            price: 101,
            quantity: 25,
          },
        ],
        timestamp: "2026-10-01T10:00:00.000Z",
      },
    });

    await gateway.stop();
  });
});
