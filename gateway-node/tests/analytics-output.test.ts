import { createServer, type Server } from "node:net";

import { afterEach, describe, expect, test } from "bun:test";

import {
  normalizeAnalyticsOutputMessage,
} from "../src/analytics/analytics-message.ts";
import { createAnalyticsClient } from "../src/analytics/analytics-client.ts";
import { createAnalyticsProvider } from "../src/analytics/analytics.provider.ts";
import type {
  GatewayAnalyticsUpdateMessage,
  GatewayRiskEventMessage,
} from "../src/analytics/analytics-message.types.ts";

const servers: Server[] = [];

afterEach(async () => {
  await Promise.all(
    servers.map(
      (server) =>
        new Promise<void>((resolve) => {
          if (!server.listening) {
            resolve();
            return;
          }
          server.close(() => resolve());
        }),
    ),
  );
  servers.length = 0;
});

function frame(payload: string): Buffer {
  const body = Buffer.from(payload, "utf8");
  const result = Buffer.alloc(4 + body.length);
  result.writeUInt32BE(body.length, 0);
  body.copy(result, 4);
  return result;
}

function outputMessage(type: "ANALYTICS_UPDATE" | "RISK_EVENT") {
  if (type === "ANALYTICS_UPDATE") {
    return JSON.stringify({
      version: 1,
      type,
      event_id: "analytics-trade-1-1",
      request_id: "analytics-trade-1-1",
      timestamp: "2026-10-02T12:00:01.000Z",
      payload: JSON.stringify({
        event_id: "analytics-trade-1-1",
        event_type: "ANALYTICS_UPDATE",
        symbol: "SIM",
        price: "100.25",
        vwap: "100.25",
        sma: "100.25",
        ema: "100.25",
        volatility: "0.0125",
        position: 10,
        realized_pnl: "0",
        unrealized_pnl: "0",
        equity: "10000",
        peak_equity: "10000",
        drawdown: "0",
        timestamp: "2026-10-02T12:00:01+00:00",
      }),
    });
  }

  return JSON.stringify({
    version: 1,
    type,
    event_id: "risk-SIM-1",
    request_id: "risk-SIM-1",
    timestamp: "2026-10-02T12:00:01.000Z",
    payload: JSON.stringify({
      event_id: "risk-SIM-1",
      event_type: "RISK_LIMIT_BREACHED",
      symbol: "SIM",
      limit_type: "MAX_DRAWDOWN",
      status: "breached",
      threshold: "100",
      warning_threshold: "80",
      current_value: "120",
      timestamp: "2026-10-02T12:00:01+00:00",
    }),
  });
}

describe("analytics output protocol", () => {
  test("normalizes analytics updates", () => {
    const message = normalizeAnalyticsOutputMessage(
      JSON.parse(outputMessage("ANALYTICS_UPDATE")),
    );

    expect(message.type).toBe("ANALYTICS_UPDATE");
    if (message.type !== "ANALYTICS_UPDATE") throw new Error("Expected ANALYTICS_UPDATE");
    expect(message.payload.equity).toBe(10000);
    expect(message.payload.drawdown).toBe(0);
    expect(message.payload.vwap).toBe(100.25);
    expect(message.payload.volatility).toBe(0.0125);
  });

  test("normalizes risk events", () => {
    const message = normalizeAnalyticsOutputMessage(
      JSON.parse(outputMessage("RISK_EVENT")),
    );

    expect(message.type).toBe("RISK_EVENT");
    if (message.type !== "RISK_EVENT") throw new Error("Expected RISK_EVENT");
    expect(message.payload.status).toBe("breached");
    expect(message.payload.limitType).toBe("MAX_DRAWDOWN");
  });

  test("receives fragmented output frames on the existing connection", async () => {
    const received: string[] = [];

    const server = createServer((socket) => {
      const payload = frame(outputMessage("ANALYTICS_UPDATE"));
      socket.write(payload.subarray(0, 3));
      socket.write(payload.subarray(3));
    });

    servers.push(server);

    await new Promise<void>((resolve) => {
      server.listen(0, "127.0.0.1", resolve);
    });

    const address = server.address();
    if (address === null || typeof address === "string") {
      throw new Error("Test server did not expose an address");
    }

    const client = createAnalyticsClient({
      host: "127.0.0.1",
      port: address.port,
      connectTimeoutMs: 1000,
      reconnectInitialDelayMs: 10,
      reconnectMaxDelayMs: 20,
      reconnectMaxAttempts: 1,
      maxQueueSize: 4,
      onAnalyticsUpdate: (message) => {
        received.push(message.eventId);
      },
    });

    client.start();

    const deadline = Date.now() + 1000;
    while (received.length === 0 && Date.now() < deadline) {
      await new Promise((resolve) => setTimeout(resolve, 5));
    }

    client.stop();

    expect(received).toEqual(["analytics-trade-1-1"]);
  });

  test("stores the latest analytics snapshot and risk state", () => {
    const provider = createAnalyticsProvider();

    provider.updateAnalytics(
      normalizeAnalyticsOutputMessage(
        JSON.parse(outputMessage("ANALYTICS_UPDATE")),
      ) as GatewayAnalyticsUpdateMessage,
    );

    expect(provider.getAnalytics()).toEqual({
      symbol: "SIM",
      price: 100.25,
      vwap: 100.25,
      sma: 100.25,
      ema: 100.25,
      volatility: 0.0125,
      position: 10,
      equity: 10000,
      realizedPnl: 0,
      unrealizedPnl: 0,
      drawdown: 0,
      riskStatus: "ok",
      timestamp: "2026-10-02T12:00:01.000Z",
    });

    provider.updateRiskEvent(
      normalizeAnalyticsOutputMessage(
        JSON.parse(outputMessage("RISK_EVENT")),
      ) as GatewayRiskEventMessage,
    );

    expect(provider.getAnalytics()?.riskStatus).toBe("breached");
  });
});
