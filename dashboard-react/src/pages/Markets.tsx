import MarketSummary from "../components/market/MarketSummary";
import OrderBook from "../components/orderbook/OrderBook";
import { useLiveTrading } from "../hooks/LiveTradingContext";
import { useOrderBook } from "../hooks/useOrderBook";

export default function Markets() {
  const { market, marketState, marketError, websocketState } = useLiveTrading();
  const { orderBook, state: orderBookState, error: orderBookError, refresh: refreshOrderBook } = useOrderBook();
  const wsConnected = websocketState === "open";

  return (
    <div>
      <header className="page-header"><span className="page-kicker">MARKET / LIVE</span><h1>Markets</h1><p>Live market state and Gateway order-book depth snapshots.</p></header>
      <section className="data-section">
        <div className="section-heading"><div><span className="panel-eyebrow">MARKET SNAPSHOT</span><h2>Current market</h2></div><span className="stream-state">WS {websocketState.toUpperCase()}</span></div>
        <MarketSummary market={market} state={marketState} error={marketError} connected={wsConnected} />
      </section>
      <section className="data-section">
        <div className="section-heading"><div><span className="panel-eyebrow">ORDER BOOK / 5.6</span><h2>Market depth</h2></div><span className="stream-state">{orderBook ? orderBook.bids.length + orderBook.asks.length + " levels" : "SNAPSHOT"}</span></div>
        <OrderBook orderBook={orderBook} state={orderBookState} error={orderBookError} onRefresh={() => void refreshOrderBook()} />
      </section>
    </div>
  );
}
