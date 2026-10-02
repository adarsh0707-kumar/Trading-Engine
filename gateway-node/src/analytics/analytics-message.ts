import {
  ANALYTICS_PROTOCOL_VERSION,
  type AnalyticsTradePayload,
  type GatewayTradeMessage,
} from "./analytics-message.types.ts";

export class AnalyticsMessageValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AnalyticsMessageValidationError";
  }
}

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
    throw new AnalyticsMessageValidationError(
      `Analytics message field '${field}' must be a non-empty string`,
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
    throw new AnalyticsMessageValidationError(
      `Analytics TRADE payload field '${field}' must be a positive number`,
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
    throw new AnalyticsMessageValidationError(
      `Analytics TRADE payload field '${field}' must be a positive integer`,
    );
  }

  return value;
}

function parseTradePayload(
  value: unknown,
): AnalyticsTradePayload {
  if (!isRecord(value)) {
    throw new AnalyticsMessageValidationError(
      "Analytics TRADE payload must be a JSON object",
    );
  }

  const takerSide = value["taker_side"];

  if (takerSide !== "BUY" && takerSide !== "SELL") {
    throw new AnalyticsMessageValidationError(
      "Analytics TRADE payload field 'taker_side' must be BUY or SELL",
    );
  }

  return {
    tradeId: requireNonEmptyString(value["trade_id"], "trade_id"),
    symbol: requireNonEmptyString(value["symbol"], "symbol"),
    price: requirePositiveNumber(value["price"], "price"),
    quantity: requirePositiveInteger(value["quantity"], "quantity"),
    takerOrderId: requireNonEmptyString(
      value["taker_order_id"],
      "taker_order_id",
    ),
    makerOrderId: requireNonEmptyString(
      value["maker_order_id"],
      "maker_order_id",
    ),
    takerSide,
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

export function normalizeGatewayTradeMessage(
  value: unknown,
): GatewayTradeMessage {
  if (!isRecord(value)) {
    throw new AnalyticsMessageValidationError(
      "Analytics message must be a JSON object",
    );
  }

  if (value["version"] !== ANALYTICS_PROTOCOL_VERSION) {
    throw new AnalyticsMessageValidationError(
      `Analytics message version must be ${ANALYTICS_PROTOCOL_VERSION}`,
    );
  }

  if (value["type"] !== "TRADE") {
    throw new AnalyticsMessageValidationError(
      "Analytics message field 'type' must be TRADE",
    );
  }

  const eventId = requireNonEmptyString(value["event_id"], "event_id");
  const requestId = requireNonEmptyString(
    value["request_id"],
    "request_id",
  );
  const timestamp = requireNonEmptyString(
    value["timestamp"],
    "timestamp",
  );

  if (eventId !== requestId) {
    throw new AnalyticsMessageValidationError(
      "Analytics TRADE event_id must equal request_id",
    );
  }

  return {
    version: ANALYTICS_PROTOCOL_VERSION,
    type: "TRADE",
    eventId,
    requestId,
    timestamp,
    payload: parseTradePayload(value["payload"]),
  };
}

export function serializeGatewayTradeMessage(
  message: GatewayTradeMessage,
): string {
  const normalized = normalizeGatewayTradeMessage(message);

  return JSON.stringify({
    version: normalized.version,
    type: normalized.type,
    event_id: normalized.eventId,
    request_id: normalized.requestId,
    timestamp: normalized.timestamp,
    // The Python MessageParser already defines the transport contract with
    // a nested JSON-string payload. Keep that wire representation stable.
    payload: JSON.stringify({
      trade_id: normalized.payload.tradeId,
      symbol: normalized.payload.symbol,
      price: normalized.payload.price,
      quantity: normalized.payload.quantity,
      taker_order_id: normalized.payload.takerOrderId,
      maker_order_id: normalized.payload.makerOrderId,
      taker_side: normalized.payload.takerSide,
      buy_order_id: normalized.payload.buyOrderId,
      sell_order_id: normalized.payload.sellOrderId,
    }),
  });
}
