import { describe, expect, test } from "bun:test";

import {
  createEngineProtocol,
  EngineProtocolError,
} from "../src/engine-protocol/engine-protocol.ts";

const encoder = new TextEncoder();

function frame(payload: string): Uint8Array {
  const payloadBytes = encoder.encode(payload);
  const result = new Uint8Array(
    4 + payloadBytes.byteLength,
  );

  result[0] =
    (payloadBytes.byteLength >>> 24) & 0xff;
  result[1] =
    (payloadBytes.byteLength >>> 16) & 0xff;
  result[2] =
    (payloadBytes.byteLength >>> 8) & 0xff;
  result[3] =
    payloadBytes.byteLength & 0xff;

  result.set(payloadBytes, 4);

  return result;
}

function engineMessage(
  overrides: Record<string, unknown> = {},
): string {
  return JSON.stringify({
    type: "TRADE",
    request_id: "trade-42",
    timestamp: "2026-10-01T12:00:00.000Z",
    payload: "{\"symbol\":\"BTC-USD\",\"price\":\"100.50\"}",
    ...overrides,
  });
}

describe("engine protocol boundary", () => {
  test("decodes, parses, and normalizes a complete engine frame", () => {
    const protocol = createEngineProtocol();

    expect(
      protocol.push(
        frame(engineMessage()),
      ),
    ).toEqual([
      {
        type: "TRADE",
        eventId: "trade-42",
        requestId: "trade-42",
        timestamp: "2026-10-01T12:00:00.000Z",
        payload:
          "{\"symbol\":\"BTC-USD\",\"price\":\"100.50\"}",
      },
    ]);
  });

  test("handles a frame split across multiple chunks", () => {
    const encoded = frame(engineMessage());
    const protocol = createEngineProtocol();

    expect(
      protocol.push(encoded.slice(0, 7)),
    ).toEqual([]);

    expect(
      protocol.push(encoded.slice(7)),
    ).toHaveLength(1);

    expect(
      protocol.push(new Uint8Array(0)),
    ).toEqual([]);
  });

  test("handles multiple engine events in one chunk", () => {
    const first = frame(
      engineMessage({
        request_id: "trade-1",
      }),
    );

    const second = frame(
      engineMessage({
        request_id: "trade-2",
      }),
    );

    const combined = new Uint8Array(
      first.byteLength + second.byteLength,
    );

    combined.set(first);
    combined.set(second, first.byteLength);

    const protocol = createEngineProtocol();

    expect(
      protocol.push(combined),
    ).toEqual([
      expect.objectContaining({
        eventId: "trade-1",
      }),
      expect.objectContaining({
        eventId: "trade-2",
      }),
    ]);
  });

  test("rejects malformed JSON", () => {
    const protocol = createEngineProtocol();

    expect(() =>
      protocol.push(
        frame("{not-valid-json"),
      ),
    ).toThrow(
      new EngineProtocolError(
        "Engine frame contains invalid JSON",
      ),
    );
  });

  test("rejects unsupported engine message types", () => {
    const protocol = createEngineProtocol();

    expect(() =>
      protocol.push(
        frame(
          engineMessage({
            type: "UNKNOWN_EVENT",
          }),
        ),
      ),
    ).toThrow(
      new EngineProtocolError(
        "Engine message field 'type' is unsupported",
      ),
    );
  });

  test("rejects malformed engine envelope fields", () => {
    const protocol = createEngineProtocol();

    expect(() =>
      protocol.push(
        frame(
          engineMessage({
            timestamp: 12345,
          }),
        ),
      ),
    ).toThrow(
      new EngineProtocolError(
        "Engine message field 'timestamp' must be a string",
      ),
    );
  });

  test("rejects an empty request id", () => {
    const protocol = createEngineProtocol();

    expect(() =>
      protocol.push(
        frame(
          engineMessage({
            request_id: "   ",
          }),
        ),
      ),
    ).toThrow(
      new EngineProtocolError(
        "Engine message field 'request_id' must not be empty",
      ),
    );
  });

  test("preserves opaque payload content", () => {
    const protocol = createEngineProtocol();

    const payload =
      "{\"symbol\":\"BTC-USD\",\"nested\":{\"price\":100.5}}";

    const events = protocol.push(
      frame(
        engineMessage({
          payload,
        }),
      ),
    );

    expect(events[0]?.payload).toBe(payload);
  });

  test("reset discards buffered partial frames", () => {
    const encoded = frame(engineMessage());
    const protocol = createEngineProtocol();

    protocol.push(encoded.slice(0, 8));
    protocol.reset();

    expect(
      protocol.push(encoded),
    ).toHaveLength(1);
  });
});
