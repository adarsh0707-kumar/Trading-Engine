export interface Trade {
  readonly tradeId: string;
  readonly symbol: string;
  readonly price: number;
  readonly quantity: number;
  readonly takerSide: "buy" | "sell";
  readonly timestamp: string;
}

export interface TradesState {
  readonly trades: readonly Trade[];
}

export interface TradesProvider {
  getTrades(): TradesState | null;
}
