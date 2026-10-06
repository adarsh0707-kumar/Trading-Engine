import type { OrderBook as OrderBookData } from "../../types";
import EmptyState from "../common/EmptyState";
import ErrorMessage from "../common/ErrorMessage";
import Loading from "../common/Loading";
import AskLevels from "./AskLevels";
import BidLevels from "./BidLevels";
import type { OrderBookState } from "../../hooks/useOrderBook";

interface OrderBookProps {
  readonly orderBook: OrderBookData | null;
  readonly state: OrderBookState;
  readonly error: string | null;
  readonly onRefresh?: () => void;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 8,
  }).format(value);
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export default function OrderBook({
  orderBook,
  state,
  error,
  onRefresh,
}: OrderBookProps) {
  if (state === "loading" && orderBook === null) {
    return <Loading message="Loading order book…" />;
  }

  if (state === "error" && orderBook === null) {
    return (
      <div className="orderbook-state">
        <ErrorMessage message={`Order book unavailable${error ? ` — ${error}` : ""}`} />
        {onRefresh && (
          <button type="button" className="orderbook-refresh" onClick={onRefresh}>
            Retry
          </button>
        )}
      </div>
    );
  }

  if (orderBook === null) {
    return <EmptyState title="No order book snapshot" message="The Gateway has not published order-book state yet." />;
  }

  const bestBid = [...orderBook.bids].sort((a, b) => b.price - a.price)[0]?.price ?? null;
  const bestAsk = [...orderBook.asks].sort((a, b) => a.price - b.price)[0]?.price ?? null;
  const spread = bestBid !== null && bestAsk !== null ? bestAsk - bestBid : null;

  return (
    <div className="orderbook">
      <div className="orderbook-toolbar">
        <div>
          <span className="panel-eyebrow">DEPTH SNAPSHOT</span>
          <strong>{orderBook.symbol}</strong>
          <span className="orderbook-updated">Updated {formatTimestamp(orderBook.timestamp)}</span>
        </div>
        <button type="button" className="orderbook-refresh" onClick={onRefresh} disabled={state === "loading"}>
          {state === "loading" ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      <div className="orderbook-stats" aria-label="Best prices">
        <div><span>Best bid</span><strong>{bestBid === null ? "—" : formatNumber(bestBid)}</strong></div>
        <div><span>Best ask</span><strong>{bestAsk === null ? "—" : formatNumber(bestAsk)}</strong></div>
        <div><span>Spread</span><strong>{spread === null ? "—" : formatNumber(spread)}</strong></div>
      </div>

      <div className="orderbook-grid">
        <section className="orderbook-side" aria-labelledby="orderbook-bids-title">
          <div className="orderbook-side-header">
            <h3 id="orderbook-bids-title">Bids</h3>
            <span>Price / Qty</span>
          </div>
          <BidLevels levels={orderBook.bids} />
        </section>

        <section className="orderbook-side" aria-labelledby="orderbook-asks-title">
          <div className="orderbook-side-header">
            <h3 id="orderbook-asks-title">Asks</h3>
            <span>Price / Qty</span>
          </div>
          <AskLevels levels={orderBook.asks} />
        </section>
      </div>
    </div>
  );
}
