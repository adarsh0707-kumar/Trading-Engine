import type {
  NormalizedEngineEvent,
  EngineMessageType,
} from "./engine-message.types.ts";
import {
  EngineMessageValidationError,
} from "./engine-message.ts";
import {
  normalizeTradeEvent,
} from "./engine-trade.ts";
import type {
  NormalizedTradeEvent,
} from "./engine-trade.types.ts";

export type NormalizedEngineEventResult =
  | NormalizedTradeEvent;

export class UnsupportedEngineEventError extends Error {
  constructor(type: EngineMessageType) {
    super(
      `Engine event type '${type}' is not supported for typed normalization`,
    );
    this.name = "UnsupportedEngineEventError";
  }
}

export function normalizeEngineEvent(
  event: NormalizedEngineEvent,
): NormalizedEngineEventResult {
  switch (event.type) {
    case "TRADE":
      return normalizeTradeEvent(event);

    case "HELLO":
    case "HEARTBEAT":
    case "ORDER":
    case "MARKET_DATA":
    case "BOOK_SNAPSHOT":
    case "ERROR":
    case "SHUTDOWN":
      throw new UnsupportedEngineEventError(
        event.type,
      );

    default:
      throw new EngineMessageValidationError(
        "Engine event type is unsupported",
      );
  }
}
