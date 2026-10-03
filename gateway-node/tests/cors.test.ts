import { describe, expect, test } from "bun:test";

import {
  createCorsOriginValidator,
  DEFAULT_CORS_ORIGINS,
  isCorsOriginAllowed,
  parseCorsOrigins,
} from "../src/security/cors.ts";

describe("CORS security", () => {
  test("uses the localhost development origin by default", () => {
    expect(parseCorsOrigins({})).toEqual([...DEFAULT_CORS_ORIGINS]);
  });

  test("parses an explicit origin allowlist", () => {
    expect(
      parseCorsOrigins({
        CORS_ORIGINS: "https://app.example.com, https://admin.example.com",
      }),
    ).toEqual([
      "https://app.example.com",
      "https://admin.example.com",
    ]);
  });

  test("keeps the legacy single-origin setting compatible", () => {
    expect(
      parseCorsOrigins({
        CORS_ORIGIN: "https://app.example.com",
      }),
    ).toEqual(["https://app.example.com"]);
  });

  test("prefers the explicit allowlist over the legacy setting", () => {
    expect(
      parseCorsOrigins({
        CORS_ORIGINS: "https://app.example.com",
        CORS_ORIGIN: "https://legacy.example.com",
      }),
    ).toEqual(["https://app.example.com"]);
  });

  test("rejects wildcard and null origins", () => {
    expect(() => parseCorsOrigins({ CORS_ORIGINS: "*" })).toThrow(
      "Invalid CORS origin",
    );
    expect(() => parseCorsOrigins({ CORS_ORIGINS: "null" })).toThrow(
      "Invalid CORS origin",
    );
  });

  test("rejects origin paths and credentials", () => {
    expect(() =>
      parseCorsOrigins({
        CORS_ORIGINS: "https://app.example.com/path",
      }),
    ).toThrow("Invalid CORS origin");

    expect(() =>
      parseCorsOrigins({
        CORS_ORIGINS: "https://user:password@app.example.com",
      }),
    ).toThrow("Invalid CORS origin");
  });

  test("rejects duplicate and empty entries", () => {
    expect(() =>
      parseCorsOrigins({
        CORS_ORIGINS: "https://app.example.com,https://app.example.com",
      }),
    ).toThrow("must not contain duplicates");

    expect(() =>
      parseCorsOrigins({
        CORS_ORIGINS: "https://app.example.com,",
      }),
    ).toThrow("only non-empty origins");
  });

  test("matches only exact configured origins", () => {
    const allowed = ["https://app.example.com"];

    expect(isCorsOriginAllowed(allowed, "https://app.example.com")).toBe(true);
    expect(isCorsOriginAllowed(allowed, "https://evil.example.com")).toBe(false);
    expect(isCorsOriginAllowed(allowed, undefined)).toBe(true);
  });

  test("creates a Fastify-compatible validator that denies untrusted origins", () => {
    const validate = createCorsOriginValidator([
      "https://app.example.com",
    ]);

    expect(validate("https://app.example.com", {})).toBe(true);
    expect(validate("https://evil.example.com", {})).toBe(false);
    expect(validate(undefined, {})).toBe(true);
  });
});
