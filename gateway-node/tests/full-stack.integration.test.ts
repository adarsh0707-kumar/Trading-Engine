import { describe, expect, test } from "bun:test";
import { createServer, type Server, type Socket } from "node:net";

import { createGatewayServer } from "../src/server.ts";

const TRADE = {
  type: "TRADE",
  event_id: "trade-event-1",
  request_id: "trade-request-1",
  timestamp: "2026-10-04T10:00:00.000Z",
  payload: {
    trade_id: "trade-1",
    symbol: "SIM",
    price: 100,
    quantity: 2,
    taker_order_id: "taker-1",
    maker_order_id: "maker-1",
    taker_side: "BUY",
    buy_order_id: "taker-1",
    sell_order_id: "maker-1",
  },
};

const ANALYTICS_UPDATE = {
  version: 1,
  type: "ANALYTICS_UPDATE",
  event_id: "analytics-event-1",
  request_id: "trade-request-1",
  timestamp: "2026-10-04T10:00:01.000Z",
  payload: {
    symbol: "SIM",
    price: 100,
    vwap: 100,
    sma: null,
    ema: null,
    position: 2,
    realized_pnl: 0,
    unrealized_pnl: 0,
    equity: 1000,
    peak_equity: 1000,
    drawdown: 0,
  },
};

function frame(value: unknown): Buffer {
  const body = Buffer.from(JSON.stringify(value), "utf8");
  const result = Buffer.alloc(4 + body.length);
  result.writeUInt32BE(body.length, 0);
  body.copy(result, 4);
  return result;
}

function waitFor<T>(
  predicate: () => T | undefined,
  timeoutMs = 5000,
): Promise<T> {
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + timeoutMs;
    const poll = (): void => {
      const value = predicate();
      if (value !== undefined) {
        resolve(value);
        return;
      }
      if (Date.now() >= deadline) {
        reject(new Error("integration condition timed out"));
        return;
      }
      setTimeout(poll, 10);
    };
    poll();
  });
}

async function listen(server: Server): Promise<number> {
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve());
  });
  const address = server.address();
  if (address === null || typeof address === "string") {
    throw new Error("server did not expose a TCP address");
  }
  return address.port;
}

async function getFreePort(): Promise<number> {
  const server = createServer();
  const port = await listen(server);
  await closeServer(server);
  return port;
}

async function closeServer(server: Server): Promise<void> {
  if (!server.listening) return;
  await new Promise<void>((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });
}

function writeAnalyticsResponse(socket: Socket): void {
  socket.write(frame(ANALYTICS_UPDATE));
}

describe("full gateway integration path", () => {
  test(
    "routes an Engine TRADE through Analytics and WebSocket consumers",
    async () => {
      let analyticsReceived: Record<string, unknown> | undefined;
      let analyticsBuffer = Buffer.alloc(0);
      let engineSocket: Socket | undefined;

      const engineServer = createServer((socket) => {
        engineSocket = socket;
        setTimeout(() => socket.write(frame(TRADE)), 250);
      });

      const analyticsServer = createServer((socket) => {
        socket.on("data", (chunk) => {
          analyticsBuffer = Buffer.concat([analyticsBuffer, Buffer.from(chunk)]);

          while (analyticsBuffer.length >= 4) {
            const size = analyticsBuffer.readUInt32BE(0);
            if (analyticsBuffer.length < size + 4) return;

            const payload = analyticsBuffer
              .subarray(4, size + 4)
              .toString("utf8");
            analyticsBuffer = analyticsBuffer.subarray(size + 4);
            analyticsReceived = JSON.parse(payload) as Record<string, unknown>;
            writeAnalyticsResponse(socket);
          }
        });
      });

      const enginePort = await listen(engineServer);
      const analyticsPort = await listen(analyticsServer);
      const gatewayPort = await getFreePort();
      const gateway = createGatewayServer({
        GATEWAY_HOST: "127.0.0.1",
        GATEWAY_PORT: String(gatewayPort),
        ENGINE_HOST: "127.0.0.1",
        ENGINE_PORT: String(enginePort),
        ANALYTICS_HOST: "127.0.0.1",
        ANALYTICS_PORT: String(analyticsPort),
        RATE_LIMIT_ENABLED: "false",
        AUTH_ENABLED: "false",
        AUTH_ENFORCEMENT_ENABLED: "false",
      });

      const received: Record<string, unknown>[] = [];
      let ws: WebSocket | undefined;

      try {
        await gateway.start();

        const address = gateway.app.server.address();
        if (address === null || typeof address === "string") {
          throw new Error("gateway did not expose a TCP address");
        }

        ws = new WebSocket(`ws://127.0.0.1:${address.port}/ws`);
        ws.onmessage = (event) => {
          received.push(JSON.parse(String(event.data)) as Record<string, unknown>);
        };

        await waitFor(() =>
          received.some((message) => message.type === "CONNECTION_READY")
            ? true
            : undefined,
        );

        ws.send(JSON.stringify({
          action: "subscribe",
          events: ["TRADE", "ANALYTICS_UPDATE"],
        }));

        await waitFor(() =>
          received.some((message) => message.type === "SUBSCRIPTION_UPDATED")
            ? true
            : undefined,
        );

        const trade = await waitFor(() =>
          received.find((message) => message.type === "TRADE"),
        );
        const analytics = await waitFor(() =>
          received.find((message) => message.type === "ANALYTICS_UPDATE"),
        );

        expect(trade).toMatchObject({
          type: "TRADE",
          eventId: "trade-event-1",
          requestId: "trade-request-1",
          payload: TRADE.payload,
        });

        expect(analytics).toMatchObject({
          type: "ANALYTICS_UPDATE",
          eventId: "analytics-event-1",
          requestId: "trade-request-1",
          payload: {
            symbol: "SIM",
            position: 2,
            equity: 1000,
          },
        });

        await waitFor(() => analyticsReceived);
        expect(analyticsReceived).toMatchObject({
          version: 1,
          type: "TRADE",
          event_id: "trade-event-1",
          request_id: "trade-request-1",
          payload: JSON.stringify(TRADE.payload),
        });

        expect(engineSocket).toBeDefined();
      } finally {
        ws?.close();
        await gateway.stop();
        await closeServer(analyticsServer);
        await closeServer(engineServer);
      }
    },
    15_000,
  );
});
