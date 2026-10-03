import { describe, expect, test } from "bun:test";

import {
  assertExactKeys,
  validateIsoTimestamp,
  validateUniqueStringArray,
} from "../src/security/input-validation.ts";

describe("external input validation", () => {
  test("rejects unexpected object fields", () => {
    expect(() =>
      assertExactKeys(
        { action: "subscribe", events: ["TRADE"], extra: true },
        ["action", "events"],
        "WebSocket message",
      ),
    ).toThrow("WebSocket message contains unsupported field 'extra'");
  });

  test("accepts strict UTC ISO timestamps", () => {
    expect(
      validateIsoTimestamp(
        "2026-10-03T12:34:56.123Z",
        "timestamp",
      ),
    ).toBe("2026-10-03T12:34:56.123Z");
  });

  test("rejects malformed timestamps", () => {
    expect(() =>
      validateIsoTimestamp(
        "2026-10-03 12:34:56",
        "timestamp",
      ),
    ).toThrow("timestamp must be an ISO-8601 UTC timestamp");
  });

  test("rejects duplicate array values", () => {
    expect(() =>
      validateUniqueStringArray(
        ["TRADE", "TRADE"],
        "events",
        3,
      ),
    ).toThrow("events must not contain duplicate values");
  });

  test("enforces array cardinality", () => {
    expect(() =>
      validateUniqueStringArray(
        ["TRADE", "ANALYTICS_UPDATE", "RISK_EVENT", "EXTRA"],
        "events",
        3,
      ),
    ).toThrow("events must contain at most 3 items");
  });
});
