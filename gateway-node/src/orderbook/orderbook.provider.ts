import type { EngineEventClient } from "../engine/engine-event-client.ts";
import type {
  OrderBookProvider,
  OrderBookState,
} from "./orderbook.types.ts";

interface RawOrderBookLevel {
  readonly price: unknown;
  readonly quantity: unknown;
}

interface RawOrderBookPayload {
  readonly symbol: unknown;
  readonly bids: unknown;
  readonly asks: unknown;
}

function parseLevels(value: unknown): OrderBookState["bids"] {
  if (!Array.isArray(value)) {
    throw new Error("Order book levels must be an array");
  }

  return value.map((level: unknown) => {
    if (typeof level !== "object" || level === null || Array.isArray(level)) {
      throw new Error("Order book level must be an object");
    }

    const item = level as RawOrderBookLevel;
    if (
      typeof item.price !== "number" ||
      !Number.isFinite(item.price) ||
      item.price <= 0 ||
      typeof item.quantity !== "number" ||
      !Number.isSafeInteger(item.quantity) ||
      item.quantity <= 0
    ) {
      throw new Error("Order book level contains invalid price or quantity");
    }

    return {
      price: item.price,
      quantity: item.quantity,
    };
  });
}

function parseSnapshot(
  payload: string,
  timestamp: string,
): OrderBookState {
  let value: unknown;
  try {
    value = JSON.parse(payload) as unknown;
  } catch {
    throw new Error("Order book snapshot contains invalid JSON");
  }

  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error("Order book snapshot must be an object");
  }

  const snapshot = value as RawOrderBookPayload;
  if (typeof snapshot.symbol !== "string" || snapshot.symbol.trim().length === 0) {
    throw new Error("Order book snapshot has an invalid symbol");
  }

  return {
    symbol: snapshot.symbol,
    bids: parseLevels(snapshot.bids),
    asks: parseLevels(snapshot.asks),
    timestamp,
  };
}

export function createOrderBookProvider(
  engineEventClient: EngineEventClient,
): OrderBookProvider {
  return {
    async getOrderBook(): Promise<OrderBookState | null> {
      try {
        const response = await engineEventClient.requestOrderBook();
        return parseSnapshot(response.payload, response.timestamp);
      } catch {
        return null;
      }
    },
  };
}
