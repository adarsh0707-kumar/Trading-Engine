import {
  createEngineFrameDecoder,
  type EngineFrameDecoder,
} from "./engine-frame.ts";
import {
  EngineMessageValidationError,
  parseAndNormalizeEngineMessage,
} from "./engine-message.ts";
import type { NormalizedEngineEvent } from "./engine-message.types.ts";

export class EngineProtocolError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "EngineProtocolError";
  }
}

export interface EngineProtocol {
  push(chunk: Uint8Array): NormalizedEngineEvent[];
  reset(): void;
}

function parseJsonFrame(
  frame: string,
): unknown {
  try {
    return JSON.parse(frame) as unknown;
  } catch {
    throw new EngineProtocolError(
      "Engine frame contains invalid JSON",
    );
  }
}

export function createEngineProtocol(
  decoder: EngineFrameDecoder = createEngineFrameDecoder(),
): EngineProtocol {
  return {
    push(chunk: Uint8Array): NormalizedEngineEvent[] {
      const frames = decoder.push(chunk);
      const events: NormalizedEngineEvent[] = [];

      for (const frame of frames) {
        try {
          events.push(
            parseAndNormalizeEngineMessage(
              parseJsonFrame(frame),
            ),
          );
        } catch (error) {
          if (error instanceof EngineProtocolError) {
            throw error;
          }

          if (
            error instanceof EngineMessageValidationError
          ) {
            throw new EngineProtocolError(
              error.message,
            );
          }

          throw new EngineProtocolError(
            "Engine frame contains an invalid message",
          );
        }
      }

      return events;
    },

    reset(): void {
      decoder.reset();
    },
  };
}
