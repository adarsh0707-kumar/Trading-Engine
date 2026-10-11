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
import type {
  EngineMarketDataPayload,
  NormalizedMarketDataEvent,
} from "./engine-market-data.types.ts";

export type NormalizedEngineEventResult =
  | NormalizedTradeEvent
  | NormalizedMarketDataEvent;

function normalizeMarketDataEvent(
  event: NormalizedEngineEvent,
): NormalizedMarketDataEvent {
  let payload: unknown;
  try {
    payload = JSON.parse(event.payload) as unknown;
  } catch {
    throw new EngineMessageValidationError(
      "Engine MARKET_DATA payload contains invalid JSON",
    );
  }

  if (
    typeof payload !== "object" ||
    payload === null ||
    Array.isArray(payload)
  ) {
    throw new EngineMessageValidationError(
      "Engine MARKET_DATA payload must be an object",
    );
  }

  const candidate = payload as Record<string, unknown>;
  if (
    typeof candidate.symbol !== "string" ||
    candidate.symbol.trim().length === 0 ||
    candidate.symbol.length > 32 ||
    typeof candidate.price !== "number" ||
    !Number.isFinite(candidate.price) ||
    candidate.price <= 0 ||
    typeof candidate.sequence !== "number" ||
    !Number.isSafeInteger(candidate.sequence) ||
    candidate.sequence < 0 ||
    Object.keys(candidate).some(
      (key) => !["symbol", "price", "sequence"].includes(key),
    )
  ) {
    throw new EngineMessageValidationError(
      "Engine MARKET_DATA payload has invalid fields",
    );
  }

  const normalizedPayload: EngineMarketDataPayload = {
    symbol: candidate.symbol,
    price: candidate.price,
    sequence: candidate.sequence,
  };

  return {
    type: "MARKET_DATA",
    eventId: event.eventId,
    requestId: event.requestId,
    timestamp: event.timestamp,
    payload: normalizedPayload,
  };
}

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

    case "MARKET_DATA":
      return normalizeMarketDataEvent(event);

    case "HELLO":
    case "HEARTBEAT":
    case "ORDER":
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
