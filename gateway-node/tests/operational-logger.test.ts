import { describe, expect, test } from "bun:test";

import { createOperationalLogger } from "../src/logging/operational-logger.ts";

describe("operational logger", () => {
  test("emits stable structured fields", () => {
    const entries: Array<{ level: string; fields: Record<string, unknown>; message: string }> = [];

    const logger = {
      info: (fields: Record<string, unknown>, message: string) => {
        entries.push({ level: "info", fields, message });
      },
      warn: (fields: Record<string, unknown>, message: string) => {
        entries.push({ level: "warn", fields, message });
      },
      error: (fields: Record<string, unknown>, message: string) => {
        entries.push({ level: "error", fields, message });
      },
    } as never;

    const operational = createOperationalLogger(logger, "engine");

    operational.info("engine_connected", {
      requestId: "req-1",
      eventId: "event-1",
      state: "connected",
      outcome: "success",
    });

    expect(entries).toEqual([
      {
        level: "info",
        fields: {
          service: "gateway",
          component: "engine",
          event: "engine_connected",
          requestId: "req-1",
          eventId: "event-1",
          state: "connected",
          outcome: "success",
        },
        message: "engine_connected",
      },
    ]);
  });

  test("keeps the canonical event field when callers pass extra fields", () => {
    const entries: Array<Record<string, unknown>> = [];
    const logger = {
      info: (fields: Record<string, unknown>) => entries.push(fields),
      warn: () => undefined,
      error: () => undefined,
    } as never;

    createOperationalLogger(logger, "http").info("request_completed", {
      event: "caller_value",
      service: "caller_value",
      requestId: "req-2",
    });

    expect(entries[0]).toEqual({
      service: "gateway",
      component: "http",
      event: "request_completed",
      requestId: "req-2",
    });
  });
});
