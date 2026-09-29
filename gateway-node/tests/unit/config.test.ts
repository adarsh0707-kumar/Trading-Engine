import { describe, expect, test } from "bun:test";
import { loadConfig } from "../../src/config/config.ts";

describe("loadConfig", () => {
  test("uses defaults when environment variables are absent", () => {
    const config = loadConfig({});

    expect(config.host).toBe("127.0.0.1");
    expect(config.port).toBe(8080);
  });

  test("loads host and port from the environment", () => {
    const config = loadConfig({
      GATEWAY_HOST: "0.0.0.0",
      GATEWAY_PORT: "9090",
    });

    expect(config.host).toBe("0.0.0.0");
    expect(config.port).toBe(9090);
  });

  test("rejects invalid ports", () => {
    expect(() =>
      loadConfig({
        GATEWAY_PORT: "70000",
      }),
    ).toThrow("Invalid GATEWAY_PORT");
  });
});
