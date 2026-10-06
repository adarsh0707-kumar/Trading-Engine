import AnalyticsChart from "../components/charts/AnalyticsChart";
import { useAnalytics } from "../hooks/useAnalytics";

function formatValue(value: number | null | undefined): string {
  return value === null || value === undefined || !Number.isFinite(value) ? "—" : value.toFixed(2);
}

function formatPercent(value: number | null | undefined): string {
  return value === null || value === undefined || !Number.isFinite(value)
    ? "—"
    : (value * 100).toFixed(2) + "%";
}

export default function Analytics() {
  const { latest, history, state, error, websocketState, refresh } = useAnalytics();

  return (
    <div className="analytics-page">
      <header className="page-header dashboard-hero">
        <div>
          <span className="page-kicker">ANALYTICS / 04</span>
          <h1>Analytics</h1>
          <p>Server-calculated indicators and live portfolio analytics from Python.</p>
        </div>
        <div className="hero-badge">
          <span className="hero-badge-dot" aria-hidden="true" />
          WS {websocketState.toUpperCase()}
        </div>
      </header>

      {state === "loading" && latest === null ? (
        <div className="state-message">Loading analytics…</div>
      ) : state === "error" && latest === null ? (
        <div className="state-message state-error analytics-state-error">
          <span>{error ?? "Analytics data is unavailable"}</span>
          <button type="button" onClick={() => void refresh()}>Retry</button>
        </div>
      ) : (
        <>
          <section className="analytics-summary" aria-label="Analytics summary">
            <article className="analytics-metric">
              <span>Last price</span>
              <strong>{formatValue(latest?.price)}</strong>
              <small>{latest?.symbol ?? "—"}</small>
            </article>
            <article className="analytics-metric">
              <span>VWAP</span>
              <strong>{formatValue(latest?.vwap)}</strong>
              <small>Volume weighted price</small>
            </article>
            <article className="analytics-metric">
              <span>SMA</span>
              <strong>{formatValue(latest?.sma)}</strong>
              <small>5-period</small>
            </article>
            <article className="analytics-metric">
              <span>EMA</span>
              <strong>{formatValue(latest?.ema)}</strong>
              <small>5-period</small>
            </article>
            <article className="analytics-metric">
              <span>Volatility</span>
              <strong>{formatPercent(latest?.volatility)}</strong>
              <small>Rolling return volatility</small>
            </article>
            <article className="analytics-metric">
              <span>Drawdown</span>
              <strong>{formatPercent(latest?.drawdown)}</strong>
              <small>{latest?.riskStatus.toUpperCase() ?? "—"}</small>
            </article>
          </section>

          <div className="analytics-grid">
            <AnalyticsChart
              title="Price & moving averages"
              points={history}
              series={[
                { key: "price", label: "Price", stroke: "chocolate" },
                { key: "vwap", label: "VWAP", stroke: "orange" },
                { key: "sma", label: "SMA", stroke: "chocolate" },
                { key: "ema", label: "EMA", stroke: "orange" },
              ]}
            />
            <AnalyticsChart
              title="Volatility"
              points={history}
              series={[{ key: "volatility", label: "Rolling volatility", stroke: "orange" }]}
              valueFormatter={formatPercent}
            />
          </div>

          <div className="analytics-grid">
            <AnalyticsChart
              title="Equity"
              points={history}
              series={[{ key: "equity", label: "Equity", stroke: "chocolate" }]}
            />
            <AnalyticsChart
              title="P&L"
              points={history}
              series={[
                { key: "realizedPnl", label: "Realized", stroke: "orange" },
                { key: "unrealizedPnl", label: "Unrealized", stroke: "chocolate" },
              ]}
            />
          </div>

          {error !== null && (
            <div className="state-message state-error analytics-inline-error">{error}</div>
          )}

          <footer className="analytics-footer">
            <span>Source: Python Analytics → Gateway</span>
            <span>Updated {latest ? new Date(latest.timestamp).toLocaleString() : "—"}</span>
            <button type="button" onClick={() => void refresh()}>Refresh snapshot</button>
          </footer>
        </>
      )}
    </div>
  );
}
