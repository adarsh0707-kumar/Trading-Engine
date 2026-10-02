import {
  ENGINE_TRADE_SIDES,
  type EngineTradePayload,
  type EngineTradeSide,
  type NormalizedTradeEvent,
} from "./engine-trade.types.ts";
import type { NormalizedEngineEvent } from "./engine-message.types.ts";
import { EngineMessageValidationError } from "./engine-message.ts";

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

function requireNonEmptyString(
  value: unknown,
  field: string,
): string {
  if (
    typeof value !== "string" ||
    value.trim().length === 0
  ) {
    throw new EngineMessageValidationError(
      `TRADE payload field '${field}' must be a non-empty string`,
    );
  }

  return value;
}

function requirePositiveNumber(
  value: unknown,
  field: string,
): number {
  if (
    typeof value !== "number" ||
    !Number.isFinite(value) ||
    value <= 0
  ) {
    throw new EngineMessageValidationError(
      `TRADE payload field '${field}' must be a positive number`,
    );
  }

  return value;
}

function requirePositiveInteger(
  value: unknown,
  field: string,
): number {
  if (
    typeof value !== "number" ||
    !Number.isSafeInteger(value) ||
    value <= 0
  ) {
    throw new EngineMessageValidationError(
      `TRADE payload field '${field}' must be a positive integer`,
    );
  }

  return value;
}

function requireTradeSide(
  value: unknown,
): EngineTradeSide {
  if (
    typeof value !== "string" ||
    !(ENGINE_TRADE_SIDES as readonly string[]).includes(value)
  ) {
    throw new EngineMessageValidationError(
      "TRADE payload field 'taker_side' must be BUY or SELL",
    );
  }

  return value as EngineTradeSide;
}

function parseTradePayload(
  payload: string,
): EngineTradePayload {
  let value: unknown;

  try {
    value = JSON.parse(payload) as unknown;
  } catch {
    throw new EngineMessageValidationError(
      "TRADE payload contains invalid JSON",
    );
  }

  if (!isRecord(value)) {
    throw new EngineMessageValidationError(
      "TRADE payload must be a JSON object",
    );
  }

  return {
    symbol: requireNonEmptyString(
      value["symbol"],
      "symbol",
    ),
    price: requirePositiveNumber(
      value["price"],
      "price",
    ),
    quantity: requirePositiveInteger(
      value["quantity"],
      "quantity",
    ),
    takerOrderId: requireNonEmptyString(
      value["taker_order_id"],
      "taker_order_id",
    ),
    makerOrderId: requireNonEmptyString(
      value["maker_order_id"],
      "maker_order_id",
    ),
    takerSide: requireTradeSide(
      value["taker_side"],
    ),
    buyOrderId: requireNonEmptyString(
      value["buy_order_id"],
      "buy_order_id",
    ),
    sellOrderId: requireNonEmptyString(
      value["sell_order_id"],
      "sell_order_id",
    ),
  };
}

export function normalizeTradeEvent(
  event: NormalizedEngineEvent,
): NormalizedTradeEvent {
  if (event.type !== "TRADE") {
    throw new EngineMessageValidationError(
      `Expected TRADE event but received ${event.type}`,
    );
  }

  const payload = parseTradePayload(event.payload);

  return {
    type: "TRADE",
    eventId: event.eventId,
    tradeId: event.eventId,
    requestId: event.requestId,
    timestamp: event.timestamp,
    payload,
  };
}
