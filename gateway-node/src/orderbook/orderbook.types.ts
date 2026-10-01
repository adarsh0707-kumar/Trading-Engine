export interface OrderBookLevel {
  readonly price: number;
  readonly quantity: number;
}

export interface OrderBookState {
  readonly symbol: string;
  readonly bids: readonly OrderBookLevel[];
  readonly asks: readonly OrderBookLevel[];
  readonly timestamp: string;
}

export interface OrderBookProvider {
  getOrderBook(): OrderBookState | null;
}
