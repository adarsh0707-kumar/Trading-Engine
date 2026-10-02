import { describe, expect, test } from "bun:test";

import {
  ConnectionFailure,
  DependencyUnavailable,
  FailureCategory,
  GatewayFailure,
  ProcessingFailure,
  ProtocolFailure,
  QueueOverflow,
  ShutdownFailure,
  TimeoutFailure,
  ValidationFailure,
  classifyFailure,
} from "../src/resilience/error-model.ts";

describe("gateway failure model", () => {
  test("exposes the stable failure taxonomy", () => {
    const categories: FailureCategory[] = [
      "connection",
      "timeout",
      "protocol",
      "validation",
      "queue_overflow",
      "dependency_unavailable",
      "processing",
      "shutdown",
    ];

    expect(categories).toEqual([
      "connection",
      "timeout",
      "protocol",
      "validation",
      "queue_overflow",
      "dependency_unavailable",
      "processing",
      "shutdown",
    ]);
  });

  test("marks recoverable and non-recoverable boundaries", () => {
    expect(new ConnectionFailure("x").recoverable).toBe(true);
    expect(new TimeoutFailure("x").recoverable).toBe(true);
    expect(new QueueOverflow("x").recoverable).toBe(true);
    expect(new DependencyUnavailable("x").recoverable).toBe(true);

    expect(new ProtocolFailure("x").recoverable).toBe(false);
    expect(new ValidationFailure("x").recoverable).toBe(false);
    expect(new ProcessingFailure("x").recoverable).toBe(false);
    expect(new ShutdownFailure("x").recoverable).toBe(false);
  });

  test("classifies unknown errors at a processing boundary", () => {
    const error = classifyFailure(new Error("boom"));

    expect(error).toBeInstanceOf(GatewayFailure);
    expect(error.category).toBe("processing");
    expect(error.recoverable).toBe(false);
    expect(error.message).toBe("boom");
  });

  test("preserves an existing gateway failure", () => {
    const failure = new ProtocolFailure("bad frame");

    expect(classifyFailure(failure)).toBe(failure);
  });

  test("supports an explicit fallback category", () => {
    const failure = classifyFailure("dependency is down", "dependency_unavailable");

    expect(failure.category).toBe("dependency_unavailable");
    expect(failure.recoverable).toBe(true);
  });
});
