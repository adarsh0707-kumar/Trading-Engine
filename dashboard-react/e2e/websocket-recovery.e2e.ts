import { expect, test, type WebSocketRoute } from "@playwright/test";

// The WebSocket recovery test requires a running Docker Compose stack
// (dashboard on 127.0.0.1:5173, gateway on 127.0.0.1:8080).  CI does not
// start the stack for this test; skip it there rather than fail.
test.skip(
  !!process.env.CI,
  "Requires a running Docker Compose stack; not available in CI",
);


test("reconnects after a gateway WebSocket drop and restores live updates", async ({ page }) => {
  const sockets: WebSocketRoute[] = [];
  const clientMessages: Array<{ socket: WebSocketRoute; message: string }> = [];
  const subscribeMessage = JSON.stringify({
    action: "subscribe",
    events: ["TRADE", "MARKET_DATA"],
  });

  await page.route("**/api/v1/market", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        data: {
          symbol: "SIM",
          lastPrice: 100.25,
          lastQuantity: 2,
          timestamp: "2026-10-16T12:00:00.000Z",
        },
      }),
    }),
  );

  await page.route("**/api/v1/trades", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ data: { trades: [] } }),
    }),
  );

  await page.routeWebSocket("**/ws", (socket) => {
    sockets.push(socket);
    socket.onMessage((message) => {
      if (typeof message === "string") clientMessages.push({ socket, message });
    });
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.locator(".hero-badge")).toContainText("WS OPEN");

  // React StrictMode may create a socket that is cleaned up before it subscribes.
  // Select a connection that actually sent the subscription instead of assuming
  // every observed socket becomes active.
  await expect.poll(
    () => clientMessages.filter(({ message }) => message === subscribeMessage).length,
  ).toBeGreaterThan(0);

  const firstSubscribedSocket = clientMessages.find(
    ({ message }) => message === subscribeMessage,
  )!.socket;
  const initialSubscriptionCount = clientMessages.filter(
    ({ message }) => message === subscribeMessage,
  ).length;

  firstSubscribedSocket.close();

  await expect.poll(
    () => clientMessages.filter(
      ({ message, socket }) => message === subscribeMessage && socket !== firstSubscribedSocket,
    ).length,
    { timeout: 10_000 },
  ).toBeGreaterThan(0);

  await expect(page.locator(".hero-badge")).toContainText("WS OPEN");

  const replacementSocket = clientMessages.find(
    ({ message, socket }) => message === subscribeMessage && socket !== firstSubscribedSocket,
  )!.socket;

  replacementSocket.send(JSON.stringify({
    type: "MARKET_DATA",
    eventId: "market-after-reconnect",
    requestId: "request-after-reconnect",
    timestamp: "2026-10-16T12:01:00.000Z",
    payload: { symbol: "SIM", price: 123.45, sequence: 2 },
  }));

  await expect(page.locator(".market-price strong")).toHaveText("123.45");
  expect(
    clientMessages.filter(({ message }) => message === subscribeMessage).length,
  ).toBeGreaterThan(initialSubscriptionCount);
});
