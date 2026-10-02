import { describe, expect, test } from "bun:test";

import {
  EngineMessageValidationError,
  normalizeEngineMessage,
  parseAndNormalizeEngineMessage,
  parseEngineMessage,
} from "../src/engine-protocol/engine-message.ts";

describe("engine message protocol", () => {
  test("parses every supported engine message type", () => {
    const types = [
      "HELLO",
      "HEARTBEAT",
      "ORDER",
      "TRADE",
      "MARKET_DATA",
      "BOOK_SNAPSHOT",
      "ERROR",
      "SHUTDOWN",
    ] as const;

    for (const type of types) {
      const message = parseEngineMessage({
        type,
        request_id: `request-${type.toLowerCase()}`,
        timestamp: "2026-10-01T12:00:00.000Z",
        payload: `payload-${type}`,
      });

      expect(message).toEqual({
        type,
        requestId: `request-${type.toLowerCase()}`,
        timestamp: "2026-10-01T12:00:00.000Z",
        payload: `payload-${type}`,
      });
    }
  });

  test("normalizes request identity into event identity", () => {
    const event = normalizeEngineMessage({
      type: "TRADE",
      requestId: " trade-42 ",
      timestamp: "2026-10-01T12:00:00.000Z",
      payload: "{\"price\":\"100.25\"}",
    });

    expect(event).toEqual({
      type: "TRADE",
      eventId: "trade-42",
      requestId: " trade-42 ",
      timestamp: "2026-10-01T12:00:00.000Z",
      payload: "{\"price\":\"100.25\"}",
    });
  });

  test("parses and normalizes a wire-shaped message", () => {
    const event = parseAndNormalizeEngineMessage({
      type: "BOOK_SNAPSHOT",
      request_id: "book-17",
      timestamp: "2026-10-01T12:00:00.000Z",
      payload: "{\"symbol\":\"BTCUSD\"}",
    });

    expect(event).toEqual({
      type: "BOOK_SNAPSHOT",
      eventId: "book-17",
      requestId: "book-17",
      timestamp: "2026-10-01T12:00:00.000Z",
      payload: "{\"symbol\":\"BTCUSD\"}",
    });
  });

  test("rejects a non-object message", () => {
    expect(() => parseEngineMessage(null)).toThrow(
      new EngineMessageValidationError(
        "Engine message must be a JSON object",
      ),
    );
  });

  test("rejects an unsupported message type", () => {
    expect(() =>
      parseEngineMessage({
        type: "START",
        request_id: "request-1",
        timestamp: "2026-10-01T12:00:00.000Z",
        payload: "",
      }),
    ).toThrow(
      new EngineMessageValidationError(
        "Engine message field 'type' is unsupported",
      ),
    );
  });

  test("rejects non-string envelope fields", () => {
    expect(() =>
      parseEngineMessage({
        type: "TRADE",
        request_id: 42,
        timestamp: "2026-10-01T12:00:00.000Z",
        payload: "",
      }),
    ).toThrow(
      new EngineMessageValidationError(
        "Engine message field 'request_id' must be a string",
      ),
    );
  });

  test("rejects an empty request id", () => {
    expect(() =>
      normalizeEngineMessage({
        type: "TRADE",
        requestId: "   ",
        timestamp: "2026-10-01T12:00:00.000Z",
        payload: "",
      }),
    ).toThrow(
      new EngineMessageValidationError(
        "Engine message field 'request_id' must not be empty",
      ),
    );
  });

  test("rejects an empty timestamp", () => {
    expect(() =>
      normalizeEngineMessage({
        type: "TRADE",
        requestId: "trade-1",
        timestamp: "   ",
        payload: "",
      }),
    ).toThrow(
      new EngineMessageValidationError(
        "Engine message field 'timestamp' must not be empty",
      ),
    );
  });

  test("preserves payload without interpreting it", () => {
    const payload = "{\"trade_id\":\"trade-1\",\"price\":100.25}";

    const event = parseAndNormalizeEngineMessage({
      type: "TRADE",
      request_id: "trade-1",
      timestamp: "2026-10-01T12:00:00.000Z",
      payload,
    });

    expect(event.payload).toBe(payload);
  });
});
