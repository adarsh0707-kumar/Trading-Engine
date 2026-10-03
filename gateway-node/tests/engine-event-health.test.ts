import { createServer, type Server } from "node:net";

import { afterEach, describe, expect, test } from "bun:test";

import { createEngineEventClient } from "../src/engine/engine-event-client.ts";

function frame(payload: string): Buffer {
  const body = Buffer.from(payload, "utf8");
  const result = Buffer.allocUnsafe(4 + body.length);
  result.writeUInt32BE(body.length, 0);
  body.copy(result, 4);
  return result;
}

const servers: Server[] = [];
const sockets: import("node:net").Socket[] = [];

afterEach(async () => {
  for (const socket of sockets) {
    socket.destroy();
  }
  sockets.length = 0;

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

describe("engine event client health", () => {
  test("exposes connection state and timestamps for engine traffic", async () => {
    const server = createServer((socket) => {
      sockets.push(socket);
      socket.write(
        frame(
          JSON.stringify({
            type: "HEARTBEAT",
            request_id: "heartbeat-1",
            timestamp: "2026-10-03T10:00:00.000Z",
            payload: "PING",
          }),
        ),
      );
    });
    servers.push(server);

    await new Promise<void>((resolve) => {
      server.listen(0, "127.0.0.1", resolve);
    });

    const address = server.address();
    if (address === null || typeof address === "string") {
      throw new Error("Test server did not expose an address");
    }

    const healthEvents: string[] = [];
    const client = createEngineEventClient({
      host: "127.0.0.1",
      port: address.port,
      connectTimeoutMs: 500,
      reconnectInitialDelayMs: 10,
      reconnectMaxDelayMs: 20,
      reconnectMaxAttempts: 1,
      onEvent: () => {},
      onHealthEvent: ({ type }) => healthEvents.push(type),
    });

    expect(client.getState()).toBe("disconnected");
    expect(client.getHealth()).toEqual({
      state: "disconnected",
      connectedAt: null,
      lastMessageAt: null,
      lastHeartbeatAt: null,
      reconnectAttempts: 0,
    });

    client.start();

    await new Promise<void>((resolve) => {
      const deadline = Date.now() + 1000;
      const check = (): void => {
        const health = client.getHealth();
        if (health.lastHeartbeatAt !== null || Date.now() >= deadline) {
          resolve();
          return;
        }
        setTimeout(check, 5);
      };
      check();
    });

    const health = client.getHealth();
    client.stop();

    expect(health.state).toBe("connected");
    expect(health.connectedAt).toBeTypeOf("number");
    expect(health.lastMessageAt).toBeTypeOf("number");
    expect(health.lastHeartbeatAt).toBeTypeOf("number");
    expect(health.lastHeartbeatAt).toBe(health.lastMessageAt);
    expect(health.reconnectAttempts).toBe(0);
    expect(healthEvents).toContain("message");
    expect(healthEvents).toContain("heartbeat");
    expect(client.getState()).toBe("disconnected");
  });

  test("tracks reconnect attempts while the engine is unavailable", async () => {
    const events: string[] = [];
    const client = createEngineEventClient({
      host: "127.0.0.1",
      port: 1,
      connectTimeoutMs: 50,
      reconnectInitialDelayMs: 10,
      reconnectMaxDelayMs: 10,
      reconnectMaxAttempts: 2,
      onEvent: () => {},
      onHealthEvent: ({ type }) => events.push(type),
    });

    client.start();
    await new Promise((resolve) => setTimeout(resolve, 80));
    const health = client.getHealth();
    client.stop();

    expect(events).toContain("connection_failure");
    expect(events).toContain("reconnect_attempt");
    expect(health.state).toBe("disconnected");
  });

  test("classifies malformed frames as protocol health events", async () => {
    const server = createServer((socket) => {
      sockets.push(socket);
      socket.write(frame("not-json"));
    });
    servers.push(server);

    await new Promise<void>((resolve) => {
      server.listen(0, "127.0.0.1", resolve);
    });

    const address = server.address();
    if (address === null || typeof address === "string") {
      throw new Error("Test server did not expose an address");
    }

    const events: string[] = [];
    const client = createEngineEventClient({
      host: "127.0.0.1",
      port: address.port,
      connectTimeoutMs: 500,
      reconnectInitialDelayMs: 10,
      reconnectMaxDelayMs: 10,
      reconnectMaxAttempts: 1,
      onEvent: () => {},
      onHealthEvent: ({ type }) => events.push(type),
    });

    client.start();
    await new Promise((resolve) => setTimeout(resolve, 50));
    client.stop();

    expect(events).toContain("protocol_failure");
  });
});
