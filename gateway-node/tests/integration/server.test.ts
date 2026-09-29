import { describe, expect, test } from "bun:test";
import { createGatewayServer } from "../../src/server.ts";

describe("gateway server lifecycle", () => {
  test("starts and stops cleanly", async () => {
    const gateway = createGatewayServer();

    await expect(gateway.start()).resolves.toBeUndefined();
    await expect(gateway.stop()).resolves.toBeUndefined();
  });

  test("start and stop are idempotent", async () => {
    const gateway = createGatewayServer();

    await gateway.start();
    await gateway.start();

    await gateway.stop();
    await gateway.stop();
  });
});
