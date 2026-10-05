import { describe, expect, test } from "bun:test";
import { GatewayApiError, createGatewayApiClient } from "./api";

const jsonResponse = (body: unknown, status = 200): Response =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

describe("Gateway REST client", () => {
  test("uses the configured base URL and unwraps the data envelope", async () => {
    const requests: string[] = [];
    const client = createGatewayApiClient({
      baseUrl: "http://gateway.test/",
      fetch: async (input) => { requests.push(String(input)); return jsonResponse({ data: { gateway: "ok", engine: "connected", analytics: "disconnected" } }); },
    });
    await expect(client.getStatus()).resolves.toEqual({ gateway: "ok", engine: "connected", analytics: "disconnected" });
    expect(requests).toEqual(["http://gateway.test/api/v1/status"]);
  });

  test("exposes every Phase 5.2 REST snapshot endpoint", async () => {
    const paths: string[] = [];
    const client = createGatewayApiClient({
      baseUrl: "http://gateway.test",
      fetch: async (input) => { paths.push(new URL(String(input)).pathname); return jsonResponse({ data: {} }); },
    });
    await client.getStatus(); await client.getEngineStatus(); await client.getMarket();
    await client.getOrderBook(); await client.getTrades(); await client.getAnalytics();
    expect(paths).toEqual(["/api/v1/status", "/api/v1/status/engine", "/api/v1/market", "/api/v1/orderbook", "/api/v1/trades", "/api/v1/analytics"]);
  });

  test("maps Gateway error envelopes to a typed error", async () => {
    const client = createGatewayApiClient({
      fetch: async () => jsonResponse({ error: { code: "DEPENDENCY_UNAVAILABLE", message: "Market state is unavailable", request_id: "req-123" } }, 503),
    });
    await expect(client.getMarket()).rejects.toMatchObject({ name: "GatewayApiError", code: "DEPENDENCY_UNAVAILABLE", requestId: "req-123", status: 503, message: "Market state is unavailable" });
  });

  test("rejects malformed successful responses", async () => {
    const client = createGatewayApiClient({ fetch: async () => jsonResponse({ status: "ok" }) });
    await expect(client.getStatus()).rejects.toMatchObject({ name: "GatewayApiError", code: "INVALID_RESPONSE", status: 200 });
  });

  test("preserves numeric response values without client-side conversion", async () => {
    const client = createGatewayApiClient({ fetch: async () => jsonResponse({ data: { symbol: "BTC-USD", lastPrice: 123456.789012, lastQuantity: 0.00012345, timestamp: "2026-10-05T10:00:00.000Z" } }) });
    await expect(client.getMarket()).resolves.toEqual({ symbol: "BTC-USD", lastPrice: 123456.789012, lastQuantity: 0.00012345, timestamp: "2026-10-05T10:00:00.000Z" });
  });

  test("maps network failures to a typed client error", async () => {
    const client = createGatewayApiClient({ fetch: async () => { throw new Error("Failed to fetch"); } });
    await expect(client.getStatus()).rejects.toMatchObject({ name: "GatewayApiError", code: "NETWORK_ERROR", status: 0, message: "Failed to fetch" });
  });
});