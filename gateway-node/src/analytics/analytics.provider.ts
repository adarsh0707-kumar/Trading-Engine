import type {
  AnalyticsProvider,
  AnalyticsSnapshot,
  RiskStatus,
} from "./analytics.types.ts";
import type {
  GatewayAnalyticsUpdateMessage,
  GatewayRiskEventMessage,
} from "./analytics-message.types.ts";

export interface MutableAnalyticsProvider extends AnalyticsProvider {
  updateAnalytics: (message: GatewayAnalyticsUpdateMessage) => void;
  updateRiskEvent: (message: GatewayRiskEventMessage) => void;
}

export function createAnalyticsProvider(): MutableAnalyticsProvider {
  let snapshot: AnalyticsSnapshot | null = null;
  let riskStatus: RiskStatus = "ok";

  return {
    getAnalytics(): AnalyticsSnapshot | null {
      if (snapshot === null) {
        return null;
      }

      return {
        ...snapshot,
        riskStatus,
      };
    },

    updateAnalytics(message): void {
      snapshot = {
        symbol: message.payload.symbol,
        price: message.payload.price,
        vwap: message.payload.vwap,
        sma: message.payload.sma,
        ema: message.payload.ema,
        volatility: message.payload.volatility,
        position: message.payload.position,
        equity: message.payload.equity,
        peakEquity: message.payload.peakEquity,
        realizedPnl: message.payload.realizedPnl,
        unrealizedPnl: message.payload.unrealizedPnl,
        drawdown: message.payload.drawdown,
        riskStatus,
        timestamp: message.timestamp,
      };
    },

    updateRiskEvent(message): void {
      riskStatus = message.payload.status;

      if (snapshot !== null) {
        snapshot = {
          ...snapshot,
          riskStatus,
          timestamp: message.timestamp,
        };
      }
    },
  };
}
