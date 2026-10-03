import { createServer, type Server } from "node:net";

import { afterEach, describe, expect, test } from "bun:test";
import WebSocket from "ws";

import { createGatewayServer } from "../src/server.ts";

function frame(payload: string): Buffer {
  const body = Buffer.from(payload, "utf8");
  const result = Buffer.allocUnsafe(4 + body.length);

  result.writeUInt32BE(body.length, 0);
  body.copy(result, 4);

  return result;
}

function helloMessage(): Buffer {
  return frame(
    JSON.stringify({
      type: "HELLO",
      request_id: "hello-engine",
      timestamp: "2026-10-02T12:00:00.000Z",
      payload: "Trading Engine",
    }),
  );
}

function tradeMessage(): Buffer {
  return frame(
    JSON.stringify({
      type: "TRADE",
      request_id: "trade-00000001-buy-1-sell-1",
      timestamp: "2026-10-02T12:00:01.000Z",
      payload: JSON.stringify({
        symbol: "SIM",
        price: 100.25,
        quantity: 10,
        taker_order_id: "buy-1",
        maker_order_id: "sell-1",
        taker_side: "BUY",
        buy_order_id: "buy-1",
        sell_order_id: "sell-1",
      }),
    }),
  );
}

function waitForOpen(socket: WebSocket): Promise<void> {
  return new Promise((resolve, reject) => {
    socket.once("open", () => resolve());
    socket.once("error", reject);
  });
}

async function getFreePort(): Promise<number> {
  const server = createServer();

  await new Promise<void>((resolve) => {
    server.listen(0, "127.0.0.1", () => resolve());
  });

  const address = server.address();

  if (address === null || typeof address === "string") {
    server.close();
    throw new Error("Port probe did not expose an address");
  }

  const port = address.port;

  await new Promise<void>((resolve) => server.close(() => resolve()));

  return port;
}

function waitForMessage(socket: WebSocket): Promise<unknown> {
  return new Promise((resolve, reject) => {
    socket.once("message", (data) => {
      try {
        resolve(JSON.parse(data.toString()));
      } catch (error) {
        reject(error);
      }
    });

    socket.once("error", reject);
  });
}

async function waitForServerAddress(
  gateway: ReturnType<typeof createGatewayServer>,
): Promise<{ host: string; port: number }> {
  const address = gateway.app.server.address();

  if (address === null || typeof address === "string") {
    throw new Error("Gateway server did not expose an address");
  }

  return {
    host: "127.0.0.1",
    port: address.port,
  };
}

describe("gateway websocket end-to-end", () => {
  let engineServer: Server | undefined;
  let gateway: ReturnType<typeof createGatewayServer> | undefined;
  let client: WebSocket | undefined;

  afterEach(async () => {
    client?.close();
    client = undefined;

    await gateway?.stop();
    gateway = undefined;

    await new Promise<void>((resolve) => {
      if (engineServer === undefined || !engineServer.listening) {
        resolve();
        return;
      }

      engineServer.close(() => resolve());
    });

    engineServer = undefined;
  });

  test("delivers a live C++-protocol TRADE to a subscribed WebSocket client", async () => {
    engineServer = createServer((socket) => {
      socket.write(helloMessage());

      setTimeout(() => {
        socket.write(tradeMessage());
      }, 25);
    });

    await new Promise<void>((resolve) => {
      engineServer?.listen(0, "127.0.0.1", () => resolve());
    });

    const engineAddress = engineServer.address();

    if (
      engineAddress === null ||
      typeof engineAddress === "string"
    ) {
      throw new Error("Engine test server did not expose an address");
    }

    const gatewayPort = await getFreePort();

    gateway = createGatewayServer({
      GATEWAY_HOST: "127.0.0.1",
      GATEWAY_PORT: String(gatewayPort),
      ENGINE_HOST: "127.0.0.1",
      ENGINE_PORT: String(engineAddress.port),
      ENGINE_CONNECT_TIMEOUT_MS: "1000",
      ENGINE_RECONNECT_INITIAL_DELAY_MS: "10",
      ENGINE_RECONNECT_MAX_DELAY_MS: "20",
      ENGINE_RECONNECT_MAX_ATTEMPTS: "1",
      WEBSOCKET_HEARTBEAT_INTERVAL_MS: "1000",
      LOG_LEVEL: "silent",
    });

    await gateway.start();

    const address = await waitForServerAddress(gateway);

    client = new WebSocket(
      `ws://${address.host}:${address.port}${gateway.config.websocket.path}`,
    );

    await waitForOpen(client);

    const readyPromise = waitForMessage(client);

    const ready = await readyPromise;

    expect(ready).toEqual({
      type: "CONNECTION_READY",
      subscriptions: [],
    });

    client.send(
      JSON.stringify({
        action: "subscribe",
        events: ["TRADE"],
      }),
    );

    const subscription = await waitForMessage(client);

    expect(subscription).toEqual({
      type: "SUBSCRIPTION_UPDATED",
      subscriptions: ["TRADE"],
    });

    const event = await waitForMessage(client);

    expect(event).toEqual({
      type: "TRADE",
      eventId: "trade-00000001-buy-1-sell-1",
      requestId: "trade-00000001-buy-1-sell-1",
      timestamp: "2026-10-02T12:00:01.000Z",
      payload: {
        symbol: "SIM",
        price: 100.25,
        quantity: 10,
        takerOrderId: "buy-1",
        makerOrderId: "sell-1",
        takerSide: "BUY",
        buyOrderId: "buy-1",
        sellOrderId: "sell-1",
      },
    });
  });
});
