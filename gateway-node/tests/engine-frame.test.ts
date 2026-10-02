import { describe, expect, test } from "bun:test";

import {
  createEngineFrameDecoder,
  ENGINE_FRAME_HEADER_SIZE,
  ENGINE_MAX_PAYLOAD_SIZE,
  EngineFrameError,
} from "../src/engine-protocol/engine-frame.ts";

function frame(payload: string): Uint8Array {
  const payloadBytes = new TextEncoder().encode(payload);
  const result = new Uint8Array(
    ENGINE_FRAME_HEADER_SIZE + payloadBytes.byteLength,
  );

  result[0] =
    (payloadBytes.byteLength >>> 24) & 0xff;
  result[1] =
    (payloadBytes.byteLength >>> 16) & 0xff;
  result[2] =
    (payloadBytes.byteLength >>> 8) & 0xff;
  result[3] =
    payloadBytes.byteLength & 0xff;

  result.set(
    payloadBytes,
    ENGINE_FRAME_HEADER_SIZE,
  );

  return result;
}

describe("engine frame decoder", () => {
  test("decodes a complete frame", () => {
    const decoder = createEngineFrameDecoder();

    expect(
      decoder.push(frame("hello")),
    ).toEqual(["hello"]);
  });

  test("waits for a partial header", () => {
    const encoded = frame("hello");
    const decoder = createEngineFrameDecoder();

    expect(
      decoder.push(encoded.slice(0, 2)),
    ).toEqual([]);

    expect(
      decoder.push(encoded.slice(2)),
    ).toEqual(["hello"]);
  });

  test("waits for a partial payload", () => {
    const encoded = frame("hello");
    const decoder = createEngineFrameDecoder();

    expect(
      decoder.push(encoded.slice(0, 5)),
    ).toEqual([]);

    expect(
      decoder.push(encoded.slice(5)),
    ).toEqual(["hello"]);
  });

  test("decodes multiple frames from one chunk", () => {
    const first = frame("first");
    const second = frame("second");

    const combined = new Uint8Array(
      first.byteLength + second.byteLength,
    );

    combined.set(first);
    combined.set(second, first.byteLength);

    const decoder = createEngineFrameDecoder();

    expect(decoder.push(combined)).toEqual([
      "first",
      "second",
    ]);
  });

  test("retains an incomplete second frame", () => {
    const first = frame("first");
    const second = frame("second");

    const partialSecond = second.slice(0, 6);

    const combined = new Uint8Array(
      first.byteLength + partialSecond.byteLength,
    );

    combined.set(first);
    combined.set(partialSecond, first.byteLength);

    const decoder = createEngineFrameDecoder();

    expect(decoder.push(combined)).toEqual(["first"]);

    expect(
      decoder.push(second.slice(6)),
    ).toEqual(["second"]);
  });

  test("supports UTF-8 payloads", () => {
    const decoder = createEngineFrameDecoder();

    expect(
      decoder.push(frame("trade: ₹100 — BTC")),
    ).toEqual(["trade: ₹100 — BTC"]);
  });

  test("rejects frames larger than 1 MiB", () => {
    const decoder = createEngineFrameDecoder();

    const header = new Uint8Array(4);
    const size =
      ENGINE_MAX_PAYLOAD_SIZE + 1;

    header[0] = (size >>> 24) & 0xff;
    header[1] = (size >>> 16) & 0xff;
    header[2] = (size >>> 8) & 0xff;
    header[3] = size & 0xff;

    expect(() =>
      decoder.push(header),
    ).toThrow(
      new EngineFrameError(
        "Engine frame payload exceeds maximum size",
      ),
    );
  });

  test("rejects invalid UTF-8 payloads", () => {
    const decoder = createEngineFrameDecoder();

    const encoded = frame("valid");
    encoded[4] = 0xff;

    expect(() =>
      decoder.push(encoded),
    ).toThrow();
  });

  test("reset discards buffered partial data", () => {
    const encoded = frame("hello");
    const decoder = createEngineFrameDecoder();

    decoder.push(encoded.slice(0, 5));
    decoder.reset();

    expect(
      decoder.push(encoded),
    ).toEqual(["hello"]);
  });
});
