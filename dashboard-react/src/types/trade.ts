export type TakerSide = "buy" | "sell" | string;

export interface Trade {
  tradeId: string;
  symbol: string;
  price: number;
  quantity: number;
  takerSide: TakerSide;
  timestamp: string;
  buyOrderId?: string;
  sellOrderId?: string;
}

export interface TradesResponse {
  trades: Trade[];
}
