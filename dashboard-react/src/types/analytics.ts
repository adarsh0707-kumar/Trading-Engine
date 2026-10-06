export type RiskStatus = "ok" | "warning" | "breached" | string;

export interface AnalyticsSnapshot {
  readonly symbol: string;
  readonly price: number;
  readonly vwap: number | null;
  readonly sma: number | null;
  readonly ema: number | null;
  readonly volatility: number | null;
  readonly position: number;
  readonly equity: number;
  readonly peakEquity: number;
  readonly realizedPnl: number;
  readonly unrealizedPnl: number;
  readonly drawdown: number;
  riskStatus: RiskStatus;
  timestamp: string;
}

export interface AnalyticsPoint extends AnalyticsSnapshot {
  readonly eventId?: string;
}
