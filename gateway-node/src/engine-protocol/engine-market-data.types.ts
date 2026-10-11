export interface EngineMarketDataPayload {
  readonly symbol: string;
  readonly price: number;
  readonly sequence: number;
}

export interface NormalizedMarketDataEvent {
  readonly type: "MARKET_DATA";
  readonly eventId: string;
  readonly requestId: string;
  readonly timestamp: string;
  readonly payload: EngineMarketDataPayload;
}
