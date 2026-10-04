export type RiskStatus = "ok" | "warning" | "breached" | string;

export interface AnalyticsSnapshot {
  equity: number;
  realizedPnl: number;
  unrealizedPnl: number;
  drawdown: number;
  riskStatus: RiskStatus;
  timestamp: string;
}
