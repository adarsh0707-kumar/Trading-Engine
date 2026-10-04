const panels = [
  {
    eyebrow: "MARKET",
    title: "Live Market",
    description: "Gateway market snapshots will appear here once the live feed is connected.",
    meta: "Awaiting /api/v1/market",
    className: "bento-panel-wide",
  },
  {
    eyebrow: "TRADES",
    title: "Recent Activity",
    description: "Executed trades will stream into this panel through the Gateway WebSocket.",
    meta: "Awaiting TRADE events",
    className: "",
  },
  {
    eyebrow: "ANALYTICS",
    title: "Performance",
    description: "Equity, P&L, drawdown, and indicator views will use Gateway analytics state.",
    meta: "Awaiting analytics snapshot",
    className: "",
  },
  {
    eyebrow: "RISK",
    title: "Risk Monitor",
    description: "Risk state and bounded risk events will be surfaced here without client-side recalculation.",
    meta: "Awaiting RISK_EVENT",
    className: "bento-panel-wide",
  },
];

export default function Dashboard() {
  return (
    <div className="dashboard-page">
      <header className="page-header dashboard-hero">
        <div>
          <span className="page-kicker">OVERVIEW / 01</span>
          <h1>Dashboard</h1>
          <p>One control surface for market state, execution activity, analytics, and risk.</p>
        </div>
        <div className="hero-badge">
          <span className="hero-badge-dot" aria-hidden="true" />
          Live architecture
        </div>
      </header>

      <section className="bento-grid" aria-label="Dashboard overview">
        <article className="bento-panel bento-panel-primary">
          <div className="panel-topline">
            <span className="panel-eyebrow">SYSTEM</span>
            <span className="panel-index">00</span>
          </div>
          <h2>Gateway connection</h2>
          <p className="panel-value">Not connected</p>
          <p className="panel-description">
            The dashboard talks only to the Gateway REST and WebSocket boundaries.
          </p>
          <div className="panel-status">
            <span className="status-dot status-dot-warning" />
            Waiting for live transport
          </div>
        </article>

        {panels.map((panel) => (
          <article
            key={panel.title}
            className={`bento-panel ${panel.className}`.trim()}
          >
            <div className="panel-topline">
              <span className="panel-eyebrow">{panel.eyebrow}</span>
              <span className="panel-index">—</span>
            </div>
            <h2>{panel.title}</h2>
            <p className="panel-description">{panel.description}</p>
            <span className="panel-meta">{panel.meta}</span>
          </article>
        ))}
      </section>
    </div>
  );
}
