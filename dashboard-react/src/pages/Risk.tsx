import FreshnessIndicator from "../components/common/FreshnessIndicator";
import { useAnalytics } from "../hooks/useAnalytics";

function formatNumber(value: number | null | undefined): string { return value == null || !Number.isFinite(value) ? "—" : value.toLocaleString(undefined, { maximumFractionDigits: 2 }); }
function formatMoney(value: number | null | undefined): string { if (value == null || !Number.isFinite(value)) return "—"; return (value > 0 ? "+" : "") + value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
function formatPercent(value: number | null | undefined): string { return value == null || !Number.isFinite(value) ? "—" : (value * 100).toFixed(2) + "%"; }
function formatDrawdownPercent(drawdown: number | null | undefined, peakEquity: number | null | undefined): string {
  if (drawdown == null || peakEquity == null || !Number.isFinite(drawdown) || !Number.isFinite(peakEquity) || peakEquity <= 0) return "—";
  return ((drawdown / peakEquity) * 100).toFixed(2) + "% from peak";
}
function statusClass(status: string | undefined): string {
  if (status === "breached") return "risk-status risk-status-breached";
  if (status === "warning") return "risk-status risk-status-warning";
  return "risk-status risk-status-ok";
}

export default function Risk() {
  const { latest, state, error, websocketState, refresh } = useAnalytics();
  const totalPnl = latest ? latest.realizedPnl + latest.unrealizedPnl : null;
  const exposure = latest ? Math.abs(latest.position * latest.price) : null;

  return (
    <div className="risk-page">
      <header className="page-header dashboard-hero">
        <div><span className="page-kicker">RISK / 05</span><h1>Portfolio & Risk</h1><p>Live portfolio exposure, P&L and server-calculated risk state.</p></div>
        <div className="hero-badge"><span className="hero-badge-dot" aria-hidden="true" />WS {websocketState.toUpperCase()}</div>
      </header>
      {state === "loading" && latest === null ? <div className="state-message">Loading portfolio state…</div> : state === "error" && latest === null ? (
        <div className="state-message state-error risk-state-error"><span>{error ?? "Portfolio data is unavailable"}</span><button type="button" onClick={() => void refresh()}>Retry</button></div>
      ) : (
        <>
          <div className="freshness-bar"><FreshnessIndicator updatedAt={latest?.timestamp} connected={websocketState === "open"} label="Portfolio risk" /><span>Source: Python Analytics → Gateway</span></div>
          <section className="risk-overview" aria-label="Portfolio overview">
            <article className="risk-card risk-card-dark"><span className="panel-eyebrow">POSITION</span><strong>{formatNumber(latest?.position)}</strong><small>{latest?.symbol ?? "—"} units</small></article>
            <article className="risk-card"><span>Mark price</span><strong>{formatNumber(latest?.price)}</strong><small>Latest analytics price</small></article>
            <article className="risk-card"><span>Exposure</span><strong>{formatMoney(exposure)}</strong><small>Absolute position × price</small></article>
            <article className="risk-card"><span>Total P&L</span><strong>{formatMoney(totalPnl)}</strong><small>Realized + unrealized</small></article>
          </section>
          <section className="risk-layout">
            <article className="risk-panel"><div className="section-heading"><div><span className="panel-eyebrow">RISK STATE</span><h2>Current protection status</h2></div><span className={statusClass(latest?.riskStatus)}>{latest?.riskStatus?.toUpperCase() ?? "UNKNOWN"}</span></div>
              <div className="risk-stat-grid"><div><span>Drawdown</span><strong>{formatMoney(latest?.drawdown)}</strong><small>{formatDrawdownPercent(latest?.drawdown, latest?.peakEquity)}</small></div><div><span>Peak equity</span><strong>{formatMoney(latest?.peakEquity)}</strong></div><div><span>Current equity</span><strong>{formatMoney(latest?.equity)}</strong></div><div><span>Volatility</span><strong>{formatPercent(latest?.volatility)}</strong></div></div>
              <div className="risk-callout"><span className="panel-eyebrow">SOURCE OF TRUTH</span><p>Risk state and analytics values are supplied by Python Analytics through the Gateway. The dashboard does not recalculate risk thresholds.</p></div>
            </article>
            <article className="risk-panel"><div className="section-heading"><div><span className="panel-eyebrow">P&L BREAKDOWN</span><h2>Performance</h2></div></div>
              <div className="pnl-stack"><div className="pnl-row"><span>Realized P&L</span><strong>{formatMoney(latest?.realizedPnl)}</strong></div><div className="pnl-row"><span>Unrealized P&L</span><strong>{formatMoney(latest?.unrealizedPnl)}</strong></div><div className="pnl-row pnl-row-total"><span>Total P&L</span><strong>{formatMoney(totalPnl)}</strong></div></div>
              <div className="risk-equity"><div><span>Equity</span><strong>{formatMoney(latest?.equity)}</strong></div><div><span>Peak</span><strong>{formatMoney(latest?.peakEquity)}</strong></div></div>
            </article>
          </section>
          {error !== null && <div className="state-message state-error risk-inline-error">{error}</div>}
          <footer className="risk-footer"><span>Updated {latest ? new Date(latest.timestamp).toLocaleString() : "—"}</span><button type="button" onClick={() => void refresh()}>Refresh snapshot</button></footer>
        </>
      )}
    </div>
  );
}
