export type RiskStatus = "ok" | "warning" | "breached";

export interface AnalyticsSnapshot {
  readonly equity: number;
  readonly realizedPnl: number;
  readonly unrealizedPnl: number;
  readonly drawdown: number;
  readonly riskStatus: RiskStatus;
  readonly timestamp: string;
}

export interface AnalyticsProvider {
  getAnalytics(): AnalyticsSnapshot | null;
}
