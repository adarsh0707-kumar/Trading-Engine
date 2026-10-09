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
  let globalRiskStatus: RiskStatus = "unknown";
  const riskStatusBySymbol = new Map<string, RiskStatus>();

  function riskStatusFor(symbol: string): RiskStatus {
    return riskStatusBySymbol.get(symbol) ?? globalRiskStatus;
  }

  return {
    getAnalytics(): AnalyticsSnapshot | null {
      if (snapshot === null) {
        return null;
      }

      return {
        ...snapshot,
        riskStatus: riskStatusFor(snapshot.symbol),
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
        riskStatus: riskStatusFor(message.payload.symbol),
        timestamp: message.timestamp,
      };
    },

    updateRiskEvent(message): void {
      const { symbol, status } = message.payload;

      if (symbol === null) {
        // A null symbol denotes a portfolio-wide event. Apply it consistently
        // to all symbols until a newer symbol-specific event overrides it.
        globalRiskStatus = status;
        riskStatusBySymbol.clear();
      } else {
        riskStatusBySymbol.set(symbol, status);
      }

      if (snapshot !== null && (symbol === null || snapshot.symbol === symbol)) {
        snapshot = {
          ...snapshot,
          riskStatus: riskStatusFor(snapshot.symbol),
          timestamp: message.timestamp,
        };
      }
    },
  };
}
