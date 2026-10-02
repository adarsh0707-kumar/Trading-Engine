export const ENGINE_TRADE_SIDES = [
  "BUY",
  "SELL",
] as const;

export type EngineTradeSide =
  (typeof ENGINE_TRADE_SIDES)[number];

export interface EngineTradePayload {
  readonly symbol: string;
  readonly price: number;
  readonly quantity: number;
  readonly takerOrderId: string;
  readonly makerOrderId: string;
  readonly takerSide: EngineTradeSide;
  readonly buyOrderId: string;
  readonly sellOrderId: string;
}

export interface NormalizedTradeEvent {
  readonly type: "TRADE";
  readonly eventId: string;
  readonly tradeId: string;
  readonly requestId: string;
  readonly timestamp: string;
  readonly payload: EngineTradePayload;
}
