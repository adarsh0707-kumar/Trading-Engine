import { useEffect, useState } from "react";
import AnalyticsChart from "../components/charts/AnalyticsChart";
import FreshnessIndicator from "../components/common/FreshnessIndicator";
import { useAnalytics } from "../hooks/useAnalytics";
import { useLiveTrading } from "../hooks/LiveTradingContext";

const ANALYTICS_STALE_AFTER_MS = 15_000;

function formatValue(value: number | null | undefined): string {
  return value === null || value === undefined || !Number.isFinite(value) ? "—" : value.toFixed(2);
}
function formatPercent(value: number | null | undefined): string {
  return value === null || value === undefined || !Number.isFinite(value) ? "—" : (value * 100).toFixed(2) + "%";
}
function formatTimestamp(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}
function isTimestampStale(value: string | null | undefined, now: number): boolean {
  if (!value) return true;
  const timestamp = new Date(value).getTime();
  return !Number.isFinite(timestamp) || now - timestamp > ANALYTICS_STALE_AFTER_MS || timestamp > now + ANALYTICS_STALE_AFTER_MS;
}

export default function Analytics() {
  const { latest, history, state, error, websocketState, refresh } = useAnalytics();
  const { market, marketState, marketError, websocketState: liveWebsocketState } = useLiveTrading();
  const [now, setNow] = useState(() => Date.now());
  const wsConnected = websocketState === "open";
  const marketConnected = liveWebsocketState === "open";
  const analyticsStale = latest !== null && isTimestampStale(latest.timestamp, now);

  useEffect(() => {
    const timer = globalThis.setInterval(() => setNow(Date.now()), 5_000);
    return () => globalThis.clearInterval(timer);
  }, []);

  return (
    <div className="analytics-page">
      <header className="page-header dashboard-hero">
        <div><span className="page-kicker">ANALYTICS / 04</span><h1>Analytics</h1><p>Live market data is sourced from the Gateway; indicators and portfolio metrics are calculated by Python Analytics.</p></div>
        <div className="hero-badge"><span className="hero-badge-dot" aria-hidden="true" />WS {liveWebsocketState.toUpperCase()}</div>
      </header>

      <section className="analytics-live-market" aria-label="Latest Gateway market price">
        <div className="section-heading">
          <div><span className="panel-eyebrow">GATEWAY MARKET FEED</span><h2>Latest Market Price</h2></div>
          {market && <FreshnessIndicator updatedAt={market.timestamp} connected={marketConnected} label="Market feed" />}
        </div>
        {marketState === "loading" && market === null ? (
          <div className="state-message">Loading latest market price…</div>
        ) : market === null ? (
          <div className="state-message state-error" role="status">Live market price is unavailable{marketError ? " — " + marketError : ""}</div>
        ) : (
          <div className="analytics-live-market-values">
            <div><span>{market.symbol} · Latest price</span><strong>{formatValue(market.lastPrice)}</strong></div>
            <div><span>Last quantity</span><strong>{formatValue(market.lastQuantity)}</strong></div>
            <div><span>Market event timestamp</span><strong>{formatTimestamp(market.timestamp)}</strong></div>
          </div>
        )}
        {marketState === "error" && market !== null && marketError && <div className="state-message state-error" role="status">Market refresh failed; showing the last available Gateway snapshot. {marketError}</div>}
      </section>

      {state === "loading" && latest === null ? (
        <div className="state-message">Loading analytics…</div>
      ) : state === "waiting" && latest === null ? (
        <div className="state-message analytics-state-waiting">
          <span>Waiting for the first analytics snapshot. The service is connected, but no trade-derived analytics update has arrived yet.</span>
          <button type="button" onClick={() => void refresh()}>Retry</button>
        </div>
      ) : state === "error" && latest === null ? (
        <div className="state-message state-error analytics-state-error"><span>{error ?? "Analytics data is unavailable"}</span><button type="button" onClick={() => void refresh()}>Retry</button></div>
      ) : (
        <>
          <div className="freshness-bar">
            <FreshnessIndicator updatedAt={latest?.timestamp} connected={wsConnected} staleAfterMs={ANALYTICS_STALE_AFTER_MS} label="Analytics" />
            <span>Source: Python Analytics → Gateway</span>
          </div>
          {analyticsStale && (
            <div className="state-message analytics-stale-warning" role="alert">
              Analytics snapshot is stale. The metrics below reflect the last analytics update at {formatTimestamp(latest?.timestamp)} and may not represent the current market. The Gateway market price above is shown separately.
            </div>
          )}
          <p className="analytics-source-note">The following indicators, equity, P&amp;L, position, and drawdown are analytics-derived values. They are not authoritative Engine risk-state or halt diagnostics.</p>
          <section className="analytics-summary" aria-label="Analytics summary">
            <article className="analytics-metric"><span>Analytics price</span><strong>{formatValue(latest?.price)}</strong><small>{latest?.symbol ?? "—"} · Python Analytics</small></article>
            <article className="analytics-metric"><span>VWAP</span><strong>{formatValue(latest?.vwap)}</strong><small>Volume weighted price</small></article>
            <article className="analytics-metric"><span>SMA</span><strong>{formatValue(latest?.sma)}</strong><small>5-period</small></article>
            <article className="analytics-metric"><span>EMA</span><strong>{formatValue(latest?.ema)}</strong><small>5-period</small></article>
            <article className="analytics-metric"><span>Volatility</span><strong>{formatPercent(latest?.volatility)}</strong><small>Rolling return volatility</small></article>
            <article className="analytics-metric"><span>Drawdown</span><strong>{formatPercent(latest?.drawdown)}</strong><small>Analytics risk status: {latest?.riskStatus.toUpperCase() ?? "—"}</small></article>
          </section>
          <div className="analytics-grid">
            <AnalyticsChart title="Price & moving averages (analytics data)" points={history} series={[{ key: "price", label: "Analytics price", stroke: "chocolate" }, { key: "vwap", label: "VWAP", stroke: "orange" }, { key: "sma", label: "SMA", stroke: "chocolate" }, { key: "ema", label: "EMA", stroke: "orange" }]} />
            <AnalyticsChart title="Volatility (analytics data)" points={history} series={[{ key: "volatility", label: "Rolling volatility", stroke: "orange" }]} valueFormatter={formatPercent} />
          </div>
          <div className="analytics-grid">
            <AnalyticsChart title="Equity (analytics-derived)" points={history} series={[{ key: "equity", label: "Analytics equity", stroke: "chocolate" }]} />
            <AnalyticsChart title="P&L (analytics-derived)" points={history} series={[{ key: "realizedPnl", label: "Realized", stroke: "orange" }, { key: "unrealizedPnl", label: "Unrealized", stroke: "chocolate" }]} />
          </div>
          {error !== null && <div className="state-message state-error analytics-inline-error">{error}</div>}
          <footer className="analytics-footer"><span>Analytics snapshot updated {latest ? formatTimestamp(latest.timestamp) : "—"}</span><button type="button" onClick={() => void refresh()}>Refresh snapshot</button></footer>
        </>
      )}
    </div>
  );
}
