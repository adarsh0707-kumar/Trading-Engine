import { describe, expect, test } from "bun:test";

import { assertRateLimit, createRateLimiter } from "../../src/security/rate-limit.ts";

describe("rate limiter", () => {
  test("allows requests up to the configured limit", () => {
    const limiter = createRateLimiter({
      maxRequests: 2,
      windowMs: 60_000,
    });

    expect(limiter.check("client-a")).toEqual({
      allowed: true,
      retryAfterSeconds: 0,
    });
    expect(limiter.check("client-a")).toEqual({
      allowed: true,
      retryAfterSeconds: 0,
    });
    expect(limiter.check("client-a").allowed).toBe(false);
  });

  test("isolates clients", () => {
    const limiter = createRateLimiter({
      maxRequests: 1,
      windowMs: 60_000,
    });

    expect(limiter.check("client-a").allowed).toBe(true);
    expect(limiter.check("client-a").allowed).toBe(false);
    expect(limiter.check("client-b").allowed).toBe(true);
  });

  test("resets buckets after the configured window", () => {
    let now = 1_000;
    const limiter = createRateLimiter({
      maxRequests: 1,
      windowMs: 5_000,
      now: () => now,
    });

    expect(limiter.check("client-a").allowed).toBe(true);
    expect(limiter.check("client-a").allowed).toBe(false);

    now = 6_000;

    expect(limiter.check("client-a")).toEqual({
      allowed: true,
      retryAfterSeconds: 0,
    });
  });

  test("returns a bounded retry-after value", () => {
    let now = 1_000;
    const limiter = createRateLimiter({
      maxRequests: 1,
      windowMs: 1_500,
      now: () => now,
    });

    expect(limiter.check("client-a").allowed).toBe(true);
    now = 1_001;

    expect(limiter.check("client-a")).toEqual({
      allowed: false,
      retryAfterSeconds: 2,
    });
  });

  test("bounds retained client buckets", () => {
    const limiter = createRateLimiter({
      maxRequests: 1,
      windowMs: 60_000,
      maxClients: 2,
    });

    limiter.check("client-a");
    limiter.check("client-b");
    limiter.check("client-c");

    expect(limiter.size()).toBe(2);
  });

  test("asserts a rate-limited failure", () => {
    const limiter = createRateLimiter({
      maxRequests: 1,
      windowMs: 60_000,
    });

    assertRateLimit(limiter, "client-a");

    expect(() => assertRateLimit(limiter, "client-a")).toThrow(
      "Rate limit exceeded",
    );
  });

  test("rejects invalid configuration", () => {
    expect(() =>
      createRateLimiter({ maxRequests: 0, windowMs: 1000 }),
    ).toThrow("maxRequests must be a positive integer");

    expect(() =>
      createRateLimiter({ maxRequests: 1, windowMs: 0 }),
    ).toThrow("windowMs must be a positive integer");

    expect(() =>
      createRateLimiter({
        maxRequests: 1,
        windowMs: 1000,
        maxClients: 0,
      }),
    ).toThrow("maxClients must be a positive integer");
  });
});
