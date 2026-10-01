export interface MarketState {
  readonly symbol: string;
  readonly lastPrice: number;
  readonly lastQuantity: number;
  readonly timestamp: string;
}

export interface MarketProvider {
  getMarket(): MarketState | null;
}
