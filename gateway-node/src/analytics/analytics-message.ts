import {
  ANALYTICS_PROTOCOL_VERSION,
  type AnalyticsRiskEventPayload,
  type AnalyticsTradePayload,
  type AnalyticsUpdatePayload,
  type GatewayAnalyticsOutputMessage,
  type GatewayAnalyticsUpdateMessage,
  type GatewayRiskEventMessage,
  type GatewayTradeMessage,
} from "./analytics-message.types.ts";

export class AnalyticsMessageValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AnalyticsMessageValidationError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requireNonEmptyString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new AnalyticsMessageValidationError(
      `Analytics message field '${field}' must be a non-empty string`,
    );
  }
  return value;
}

function requirePositiveNumber(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
    throw new AnalyticsMessageValidationError(
      `Analytics TRADE payload field '${field}' must be a positive number`,
    );
  }
  return value;
}

function requirePositiveInteger(value: unknown, field: string): number {
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

function requireFiniteNumber(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new AnalyticsMessageValidationError(
      `Analytics message field '${field}' must be a finite number`,
    );
  }
  return value;
}

function requireOutputNumber(value: unknown, field: string): number {
  if (typeof value === "number") {
    return requireFiniteNumber(value, field);
  }

  if (typeof value === "string" && value.trim().length > 0) {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  throw new AnalyticsMessageValidationError(
    `Analytics output field '${field}' must be a finite number or numeric string`,
  );
}

function requirePositiveOutputNumber(value: unknown, field: string): number {
  const parsed = requireOutputNumber(value, field);
  if (parsed <= 0) {
    throw new AnalyticsMessageValidationError(
      `Analytics output field '${field}' must be greater than zero`,
    );
  }
  return parsed;
}

function requireNullableFiniteNumber(
  value: unknown,
  field: string,
): number | null {
  if (value === null) {
    return null;
  }
  return requireOutputNumber(value, field);
}

function parseJsonPayload(value: unknown, context: string): Record<string, unknown> {
  if (isRecord(value)) {
    return value;
  }

  if (typeof value !== "string") {
    throw new AnalyticsMessageValidationError(
      `Analytics ${context} payload must be a JSON string or object`,
    );
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(value);
  } catch {
    throw new AnalyticsMessageValidationError(
      `Analytics ${context} payload must contain valid JSON`,
    );
  }

  if (!isRecord(parsed)) {
    throw new AnalyticsMessageValidationError(
      `Analytics ${context} payload must decode to a JSON object`,
    );
  }

  return parsed;
}

function parseTradePayload(value: unknown): AnalyticsTradePayload {
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
    price: requirePositiveOutputNumber(value["price"], "price"),
    quantity: requirePositiveInteger(value["quantity"], "quantity"),
    takerOrderId: requireNonEmptyString(value["taker_order_id"], "taker_order_id"),
    makerOrderId: requireNonEmptyString(value["maker_order_id"], "maker_order_id"),
    takerSide,
    buyOrderId: requireNonEmptyString(value["buy_order_id"], "buy_order_id"),
    sellOrderId: requireNonEmptyString(value["sell_order_id"], "sell_order_id"),
  };
}

function parseEnvelope(value: unknown): {
  eventId: string;
  requestId: string;
  timestamp: string;
  type: string;
  payload: Record<string, unknown>;
} {
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

  const eventId = requireNonEmptyString(value["event_id"], "event_id");
  const requestId = requireNonEmptyString(value["request_id"], "request_id");
  const timestamp = requireNonEmptyString(value["timestamp"], "timestamp");
  const type = requireNonEmptyString(value["type"], "type");

  return {
    eventId,
    requestId,
    timestamp,
    type,
    payload: parseJsonPayload(value["payload"], type),
  };
}

export function normalizeGatewayTradeMessage(
  value: unknown,
): GatewayTradeMessage {
  const envelope = parseEnvelope(value);

  if (envelope.type !== "TRADE") {
    throw new AnalyticsMessageValidationError(
      "Analytics message field 'type' must be TRADE",
    );
  }

  if (envelope.eventId !== envelope.requestId) {
    throw new AnalyticsMessageValidationError(
      "Analytics TRADE event_id must equal request_id",
    );
  }

  return {
    version: ANALYTICS_PROTOCOL_VERSION,
    type: "TRADE",
    eventId: envelope.eventId,
    requestId: envelope.requestId,
    timestamp: envelope.timestamp,
    payload: parseTradePayload(envelope.payload),
  };
}

function parseAnalyticsUpdatePayload(
  value: Record<string, unknown>,
): AnalyticsUpdatePayload {
  return {
    symbol: requireNonEmptyString(value["symbol"], "symbol"),
    price: requirePositiveOutputNumber(value["price"], "price"),
    vwap: requireNullableFiniteNumber(value["vwap"], "vwap"),
    sma: requireNullableFiniteNumber(value["sma"], "sma"),
    ema: requireNullableFiniteNumber(value["ema"], "ema"),
    volatility: requireNullableFiniteNumber(value["volatility"], "volatility"),
    position: requireOutputNumber(value["position"], "position"),
    realizedPnl: requireOutputNumber(value["realized_pnl"], "realized_pnl"),
    unrealizedPnl: requireOutputNumber(value["unrealized_pnl"], "unrealized_pnl"),
    equity: requireOutputNumber(value["equity"], "equity"),
    peakEquity: requireOutputNumber(value["peak_equity"], "peak_equity"),
    drawdown: requireOutputNumber(value["drawdown"], "drawdown"),
  };
}

export function normalizeAnalyticsOutputMessage(
  value: unknown,
): GatewayAnalyticsOutputMessage {
  const envelope = parseEnvelope(value);

  if (envelope.type === "ANALYTICS_UPDATE") {
    return {
      version: ANALYTICS_PROTOCOL_VERSION,
      type: "ANALYTICS_UPDATE",
      eventId: envelope.eventId,
      requestId: envelope.requestId,
      timestamp: envelope.timestamp,
      payload: parseAnalyticsUpdatePayload(envelope.payload),
    };
  }

  if (envelope.type === "RISK_EVENT") {
    const status = envelope.payload["status"];
    if (status !== "warning" && status !== "breached") {
      throw new AnalyticsMessageValidationError(
        "Analytics RISK_EVENT payload field 'status' must be warning or breached",
      );
    }

    const eventType = envelope.payload["event_type"];
    if (
      eventType !== "RISK_LIMIT_WARNING" &&
      eventType !== "RISK_LIMIT_BREACHED"
    ) {
      throw new AnalyticsMessageValidationError(
        "Analytics RISK_EVENT payload contains an unsupported event_type",
      );
    }

    const symbol = envelope.payload["symbol"];
    if (symbol !== null && typeof symbol !== "string") {
      throw new AnalyticsMessageValidationError(
        "Analytics RISK_EVENT payload field 'symbol' must be a string or null",
      );
    }

    return {
      version: ANALYTICS_PROTOCOL_VERSION,
      type: "RISK_EVENT",
      eventId: envelope.eventId,
      requestId: envelope.requestId,
      timestamp: envelope.timestamp,
      payload: {
        eventId: requireNonEmptyString(envelope.payload["event_id"], "event_id"),
        eventType,
        symbol,
        limitType: requireNonEmptyString(envelope.payload["limit_type"], "limit_type"),
        status,
        threshold: requireOutputNumber(envelope.payload["threshold"], "threshold"),
        warningThreshold: requireOutputNumber(
          envelope.payload["warning_threshold"],
          "warning_threshold",
        ),
        currentValue: requireOutputNumber(
          envelope.payload["current_value"],
          "current_value",
        ),
        timestamp: requireNonEmptyString(
          envelope.payload["timestamp"],
          "timestamp",
        ),
      },
    };
  }

  throw new AnalyticsMessageValidationError(
    `Unsupported analytics output message type: ${envelope.type}`,
  );
}

export function serializeGatewayTradeMessage(
  message: GatewayTradeMessage,
): string {
  const wireMessage = {
    version: message.version,
    type: message.type,
    event_id: message.eventId,
    request_id: message.requestId,
    timestamp: message.timestamp,
    payload: JSON.stringify({
      trade_id: message.payload.tradeId,
      symbol: message.payload.symbol,
      price: message.payload.price,
      quantity: message.payload.quantity,
      taker_order_id: message.payload.takerOrderId,
      maker_order_id: message.payload.makerOrderId,
      taker_side: message.payload.takerSide,
      buy_order_id: message.payload.buyOrderId,
      sell_order_id: message.payload.sellOrderId,
    }),
  };

  normalizeGatewayTradeMessage(wireMessage);

  return JSON.stringify(wireMessage);
}
