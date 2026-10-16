import { describe, expect, test } from "bun:test";

import { createGatewayServer } from "../../src/server.ts";
import type {
  AnalyticsProvider,
  AnalyticsSnapshot,
} from "../../src/analytics/analytics.types.ts";

interface ErrorResponse {
  readonly error: {
    readonly code: string;
    readonly message: string;
    readonly request_id: string;
  };
}

interface AnalyticsResponse {
  readonly data: AnalyticsSnapshot;
}

describe("GET /api/v1/analytics", () => {
  test("returns dependency unavailable when analytics data is unavailable", async () => {
    const gateway = createGatewayServer();

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/v1/analytics",
    });

    expect(response.statusCode).toBe(503);

    const body = response.json() as ErrorResponse;

    expect(body.error.code).toBe("DEPENDENCY_UNAVAILABLE");
    expect(body.error.message).toBe("Required dependency is unavailable");
    expect(body.error.request_id).toBeTruthy();

    await gateway.stop();
  });

  test("returns the analytics snapshot from the injected provider", async () => {
    const analyticsProvider: AnalyticsProvider = {
      getAnalytics: () => ({
        symbol: "SIM",
        price: 100.25,
        vwap: 100.2,
        sma: 100.1,
        ema: 100.15,
        volatility: 0.0125,
        position: 5,
        equity: 10500,
        peakEquity: 10600,
        realizedPnl: 250,
        unrealizedPnl: 125,
        drawdown: 75,
        riskStatus: "ok",
        timestamp: "2026-10-01T10:00:00.000Z",
      }),
    };

    const gateway = createGatewayServer(process.env, {
      analyticsProvider,
    });

    const response = await gateway.app.inject({
      method: "GET",
      url: "/api/v1/analytics",
    });

    expect(response.statusCode).toBe(200);

    const body = response.json() as AnalyticsResponse;

    expect(body).toEqual({
      data: {
        symbol: "SIM",
        price: 100.25,
        vwap: 100.2,
        sma: 100.1,
        ema: 100.15,
        volatility: 0.0125,
        position: 5,
        equity: 10500,
        peakEquity: 10600,
        realizedPnl: 250,
        unrealizedPnl: 125,
        drawdown: 75,
        riskStatus: "ok",
        timestamp: "2026-10-01T10:00:00.000Z",
      },
    });

    await gateway.stop();
  });
});
