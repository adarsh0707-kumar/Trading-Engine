export type RiskStatus = "unknown" | "ok" | "warning" | "breached";

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
  readonly riskStatus: RiskStatus;
  readonly timestamp: string;
}

export interface AnalyticsProvider {
  getAnalytics(): AnalyticsSnapshot | null;
}
