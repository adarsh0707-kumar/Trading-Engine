import MarketSummary from "../components/market/MarketSummary";
import RecentTrades from "../components/market/RecentTrades";
import { useLiveTrading } from "../hooks/LiveTradingContext";

export default function Dashboard() {
  const {
    market,
    trades,
    marketState,
    tradesState,
    marketError,
    tradesError,
    websocketState,
  } = useLiveTrading();

  return (
    <div className="dashboard-page">
      <header className="page-header dashboard-hero">
        <div>
          <span className="page-kicker">OVERVIEW / 01</span>
          <h1>Dashboard</h1>
          <p>Live market state and execution activity through the Gateway.</p>
        </div>
        <div className="hero-badge">
          <span className="hero-badge-dot" aria-hidden="true" />
          WS {websocketState.toUpperCase()}
        </div>
      </header>

      <section className="dashboard-live-grid" aria-label="Live trading overview">
        <article className="live-card live-card-market">
          <div className="section-heading">
            <div>
              <span className="panel-eyebrow">MARKET</span>
              <h2>Live Market</h2>
            </div>
          </div>
          <MarketSummary market={market} state={marketState} error={marketError} />
        </article>

        <article className="live-card">
          <div className="section-heading">
            <div>
              <span className="panel-eyebrow">TRADES</span>
              <h2>Recent Activity</h2>
            </div>
            <span className="stream-state">{trades.length} shown</span>
          </div>
          <RecentTrades trades={trades.slice(0, 8)} state={tradesState} error={tradesError} />
        </article>
      </section>
    </div>
  );
}
