import { describe, expect, test } from "bun:test";
import { isAnalyticsDataNotReady } from "./useAnalytics";
import { GatewayApiError } from "../services/api";

describe("analytics initial snapshot state", () => {
  test("classifies DATA_NOT_READY as waiting rather than a service failure", () => {
    expect(
      isAnalyticsDataNotReady(
        new GatewayApiError("Analytics is waiting for its first data snapshot", {
          code: "DATA_NOT_READY",
          status: 503,
        }),
      ),
    ).toBe(true);
  });

  test("does not classify genuine dependency failures as waiting", () => {
    expect(
      isAnalyticsDataNotReady(
        new GatewayApiError("Required dependency is unavailable", {
          code: "DEPENDENCY_UNAVAILABLE",
          status: 503,
        }),
      ),
    ).toBe(false);
    expect(isAnalyticsDataNotReady(new Error("Network failure"))).toBe(false);
  });
});
