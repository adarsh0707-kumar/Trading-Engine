export const ENGINE_FRAME_HEADER_SIZE = 4;
import { MAX_TRANSPORT_PAYLOAD_BYTES } from "../security/input-validation.ts";

export const ENGINE_MAX_PAYLOAD_SIZE = MAX_TRANSPORT_PAYLOAD_BYTES;

export class EngineFrameError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "EngineFrameError";
  }
}

export interface EngineFrameDecoder {
  push(chunk: Uint8Array): string[];
  reset(): void;
}

function readUint32BigEndian(
  buffer: Uint8Array,
): number {
  if (buffer.byteLength < ENGINE_FRAME_HEADER_SIZE) {
    throw new EngineFrameError(
      "Engine frame header is incomplete",
    );
  }

  const first = buffer[0];
  const second = buffer[1];
  const third = buffer[2];
  const fourth = buffer[3];

  if (
    first === undefined ||
    second === undefined ||
    third === undefined ||
    fourth === undefined
  ) {
    throw new EngineFrameError(
      "Engine frame header is incomplete",
    );
  }

  return (
    (first << 24) |
    (second << 16) |
    (third << 8) |
    fourth
  ) >>> 0;
}

function decodeUtf8(
  payload: Uint8Array,
): string {
  return new TextDecoder("utf-8", {
    fatal: true,
  }).decode(payload);
}

export function createEngineFrameDecoder(): EngineFrameDecoder {
  let buffer = new Uint8Array(0);

  return {
    push(chunk: Uint8Array): string[] {
      if (chunk.byteLength === 0) {
        return [];
      }

      const combined = new Uint8Array(
        buffer.byteLength + chunk.byteLength,
      );

      combined.set(buffer);
      combined.set(chunk, buffer.byteLength);
      buffer = combined;

      const frames: string[] = [];

      while (
        buffer.byteLength >= ENGINE_FRAME_HEADER_SIZE
      ) {
        const payloadSize =
          readUint32BigEndian(buffer);

        if (payloadSize > ENGINE_MAX_PAYLOAD_SIZE) {
          throw new EngineFrameError(
            "Engine frame payload exceeds maximum size",
          );
        }

        const totalSize =
          ENGINE_FRAME_HEADER_SIZE + payloadSize;

        if (buffer.byteLength < totalSize) {
          break;
        }

        const payload =
          buffer.slice(
            ENGINE_FRAME_HEADER_SIZE,
            totalSize,
          );

        frames.push(decodeUtf8(payload));

        buffer = buffer.slice(totalSize);
      }

      return frames;
    },

    reset(): void {
      buffer = new Uint8Array(0);
    },
  };
}
