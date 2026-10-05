import MarketSummary from "../components/market/MarketSummary";
import { useLiveTrading } from "../hooks/LiveTradingContext";

export default function Markets() {
  const { market, marketState, marketError, websocketState } = useLiveTrading();

  return (
    <div>
      <header className="page-header">
        <span className="page-kicker">MARKET / LIVE</span>
        <h1>Markets</h1>
        <p>Live market state sourced from the Gateway REST snapshot and TRADE stream.</p>
      </header>

      <section className="data-section">
        <div className="section-heading">
          <div>
            <span className="panel-eyebrow">MARKET SNAPSHOT</span>
            <h2>Current market</h2>
          </div>
          <span className="stream-state">WS {websocketState.toUpperCase()}</span>
        </div>
        <MarketSummary market={market} state={marketState} error={marketError} />
      </section>
    </div>
  );
}
