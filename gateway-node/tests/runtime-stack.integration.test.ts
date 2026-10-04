import { describe, expect, test } from "bun:test";

const baseUrl = process.env.GATEWAY_RUNTIME_URL ?? "http://127.0.0.1:8080";
const wsUrl = baseUrl.replace(/^http/, "ws") + "/ws";

async function waitForReady(timeoutMs = 30_000): Promise<void> {
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    try {
      const health = await fetch(baseUrl + "/api/health");
      if (health.ok) {
        const ready = await fetch(baseUrl + "/api/ready");
        if (ready.ok) return;
      }
    } catch {
      // Runtime services are expected to take a short time to start.
    }

    await Bun.sleep(250);
  }

  throw new Error("gateway readiness check timed out");
}

function waitForMessage(
  messages: Record<string, unknown>[],
  predicate: (message: Record<string, unknown>) => boolean,
  timeoutMs = 30_000,
): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + timeoutMs;

    const poll = (): void => {
      const message = messages.find(predicate);
      if (message) {
        resolve(message);
        return;
      }

      if (Date.now() >= deadline) {
        reject(new Error("runtime integration message timed out"));
        return;
      }

      setTimeout(poll, 100);
    };

    poll();
  });
}

const runtimeIntegrationEnabled = process.env.RUN_RUNTIME_INTEGRATION === "true";

describe.skipIf(!runtimeIntegrationEnabled)("runtime full-stack integration", () => {
  test(
    "routes a real C++ Engine trade through Analytics, PostgreSQL, and WebSocket",
    async () => {
      await waitForReady();

      const messages: Record<string, unknown>[] = [];
      const ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          messages.push(JSON.parse(String(event.data)) as Record<string, unknown>);
        } catch {
          // Ignore non-JSON frames; the gateway contract is JSON.
        }
      };

      try {
        await new Promise<void>((resolve, reject) => {
          const timeout = setTimeout(
            () => reject(new Error("WebSocket connection timed out")),
            10_000,
          );

          ws.addEventListener("open", () => {
            clearTimeout(timeout);
            resolve();
          }, { once: true });

          ws.addEventListener("error", () => {
            clearTimeout(timeout);
            reject(new Error("WebSocket connection failed"));
          }, { once: true });
        });

        ws.send(JSON.stringify({
          action: "subscribe",
          events: ["TRADE", "ANALYTICS_UPDATE"],
        }));

        await waitForMessage(
          messages,
          (message) => message.type === "SUBSCRIPTION_UPDATED",
        );

        const trade = await waitForMessage(
          messages,
          (message) => message.type === "TRADE",
        );

        const analytics = await waitForMessage(
          messages,
          (message) => message.type === "ANALYTICS_UPDATE",
        );

        expect(trade.payload).toMatchObject({
          symbol: "SIM",
        });

        expect(analytics.payload).toMatchObject({
          symbol: "SIM",
        });

        expect(typeof trade.eventId).toBe("string");
        expect(typeof trade.requestId).toBe("string");
        expect(typeof analytics.eventId).toBe("string");
        expect(typeof analytics.requestId).toBe("string");
      } finally {
        ws.close();
      }
    },
    45_000,
  );
});
