import RecentTrades from "../components/market/RecentTrades";
import { useLiveTrading } from "../hooks/LiveTradingContext";

export default function Trades() {
  const { trades, tradesState, tradesError, websocketState } = useLiveTrading();

  return (
    <div>
      <header className="page-header">
        <span className="page-kicker">TRADES / LIVE</span>
        <h1>Trades</h1>
        <p>Recent executed trades with live TRADE events from the Gateway.</p>
      </header>

      <section className="data-section">
        <div className="section-heading">
          <div>
            <span className="panel-eyebrow">RECENT ACTIVITY</span>
            <h2>Executed trades</h2>
          </div>
          <span className="stream-state">WS {websocketState.toUpperCase()}</span>
        </div>
        <RecentTrades trades={trades} state={tradesState} error={tradesError} />
      </section>
    </div>
  );
}
