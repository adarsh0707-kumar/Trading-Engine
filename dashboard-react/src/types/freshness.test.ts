import { describe, expect, test } from "bun:test";
import { formatFreshnessAge, getFreshness } from "./freshness";

describe("dashboard freshness", () => {
  test("marks recent connected data as fresh", () => {
    expect(getFreshness("2026-10-07T10:00:00.000Z", { now: Date.parse("2026-10-07T10:00:10.000Z") })).toMatchObject({
      state: "fresh",
      ageMs: 10_000,
    });
  });

  test("marks old data as stale", () => {
    expect(getFreshness("2026-10-07T10:00:00.000Z", { now: Date.parse("2026-10-07T10:00:20.000Z") }).state).toBe("stale");
  });

  test("marks valid data stale when its live connection is down", () => {
    expect(getFreshness("2026-10-07T10:00:00.000Z", { now: Date.parse("2026-10-07T10:00:02.000Z"), connected: false }).state).toBe("stale");
  });

  test("handles missing data explicitly", () => {
    expect(getFreshness(null)).toEqual({ state: "unknown", updatedAt: null, ageMs: null });
    expect(formatFreshnessAge(null)).toBe("No data");
  });
});
