import type { MarketSnapshot } from "../../types";
import type { OrderBook } from "../../types/orderbook";

interface MarketSummaryProps {
  readonly market: MarketSnapshot | null;
  readonly orderBook?: OrderBook | null;
  readonly state: "loading" | "ready" | "error";
  readonly error: string | null;
}

function formatPrice(value: number): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 8,
  }).format(value);
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export default function MarketSummary({
  market,
  orderBook,
  state,
  error,
}: MarketSummaryProps) {
  const bestBid = orderBook?.bids[0]?.price ?? null;
  const bestAsk = orderBook?.asks[0]?.price ?? null;
  const spread =
    bestBid !== null && bestAsk !== null ? bestAsk - bestBid : null;

  if (state === "loading") {
    return <div className="state-message">Loading market snapshot…</div>;
  }

  if (state === "error" && market === null) {
    return (
      <div className="state-message state-error">
        Market unavailable{error ? " — " + error : ""}
      </div>
    );
  }

  if (market === null) {
    return <div className="state-message">No market data available.</div>;
  }

  return (
    <div className="market-summary" aria-label="Live market summary">
      <div className="market-symbol">
        <span className="panel-eyebrow">SYMBOL</span>
        <strong>{market.symbol}</strong>
      </div>
      <div className="market-price">
        <span className="panel-eyebrow">LAST PRICE</span>
        <strong>{formatPrice(market.lastPrice)}</strong>
      </div>
      <div className="market-metric">
        <span>Last quantity</span>
        <strong>{formatPrice(market.lastQuantity)}</strong>
      </div>
      <div className="market-metric">
        <span>Bid</span>
        <strong>{bestBid !== null ? formatPrice(bestBid) : "—"}</strong>
      </div>
      <div className="market-metric">
        <span>Ask</span>
        <strong>{bestAsk !== null ? formatPrice(bestAsk) : "—"}</strong>
      </div>
      <div className="market-metric">
        <span>Spread</span>
        <strong>{spread !== null ? formatPrice(spread) : "—"}</strong>
      </div>
      <div className="market-timestamp">
        Updated {formatTimestamp(market.timestamp)}
      </div>
    </div>
  );
}
